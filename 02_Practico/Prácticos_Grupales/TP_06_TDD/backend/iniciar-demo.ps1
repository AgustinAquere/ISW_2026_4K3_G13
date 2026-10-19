<#
.SYNOPSIS
    Levanta EcoHarmony Park con un solo comando: la app y un link público
    (https) con un túnel de Cloudflare.

.DESCRIPTION
    1. La primera vez crea el entorno virtual .venv e instala las dependencias.
    2. Verifica que exista .env (si no, lo copia de .env.example y avisa).
    3. Abre un túnel rápido de Cloudflare hacia la app y espera su link https.
    4. Escribe ese link en URL_PUBLICA del .env: es a donde vuelve Mercado Pago
       después de pagar (con https, Mercado Pago vuelve solo al sitio).
    5. Levanta la app. Ctrl+C apaga la app y el túnel.

    El link cambia cada vez que se levanta el túnel y funciona mientras esta
    ventana esté abierta. Cualquiera que lo tenga puede usar la app:
    compartilo solo con el grupo.

.PARAMETER Local
    Sin túnel: la app queda solo en http://127.0.0.1:8000/.

.PARAMETER Puerto
    Puerto local de la app (por defecto, 8000).

.EXAMPLE
    .\iniciar-demo.ps1

.EXAMPLE
    .\iniciar-demo.ps1 -Local
#>
param(
    [switch]$Local,
    [int]$Puerto = 8000
)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

$Utf8SinBom = New-Object System.Text.UTF8Encoding $false
$RutaEnv = Join-Path $PSScriptRoot ".env"
$PythonVenv = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

function Escribir-Paso([string]$Texto) {
    Write-Host ""
    Write-Host "==> $Texto" -ForegroundColor Green
}

function Buscar-PythonBase {
    # Una versión normal de Python 3.12 o 3.13: "py" a veces elige la
    # versión experimental 3.13t, en la que fallan las dependencias.
    foreach ($Version in @("3.13", "3.12")) {
        try {
            & py "-$Version" -c "import sys" *> $null
            if ($LASTEXITCODE -eq 0) { return @("py", "-$Version") }
        } catch { }
    }
    $Python = Get-Command python -ErrorAction SilentlyContinue
    if ($Python) { return @($Python.Source) }
    throw "No se encontró Python 3.12 o 3.13. Instalalo desde https://www.python.org/downloads/ y volvé a ejecutar el script."
}

function Preparar-Entorno {
    if (Test-Path $PythonVenv) { return }
    Escribir-Paso "Primera vez: creando el entorno virtual e instalando dependencias (puede tardar unos minutos)"
    $Base = Buscar-PythonBase
    $Ejecutable = $Base[0]
    $Argumentos = @($Base | Select-Object -Skip 1) + @("-m", "venv", ".venv")
    & $Ejecutable @Argumentos
    if ($LASTEXITCODE -ne 0) { throw "No se pudo crear el entorno virtual .venv." }
    & $PythonVenv -m pip install --disable-pip-version-check -q -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw "No se pudieron instalar las dependencias (requirements.txt)." }
}

function Verificar-Env {
    if (Test-Path $RutaEnv) { return }
    Copy-Item (Join-Path $PSScriptRoot ".env.example") $RutaEnv
    Write-Host ""
    Write-Host "No había .env: se copió .env.example. Sin credenciales, Mercado Pago es el simulador y los mails se escriben en esta consola." -ForegroundColor Yellow
    Write-Host "Para usar Mercado Pago de prueba y Gmail, completá .env (ver CONFIGURACION_CREDENCIALES.md)." -ForegroundColor Yellow
}

function Verificar-Puerto {
    $Ocupado = Get-NetTCPConnection -LocalPort $Puerto -State Listen -ErrorAction SilentlyContinue
    if ($Ocupado) {
        throw "El puerto $Puerto ya está en uso (¿la app ya está corriendo en otra ventana?). Cerrala o usá -Puerto con otro número."
    }
}

function Buscar-Cloudflared {
    $Comando = Get-Command cloudflared -ErrorAction SilentlyContinue
    if ($Comando) { return $Comando.Source }
    foreach ($Carpeta in @(${env:ProgramFiles(x86)}, $env:ProgramFiles)) {
        if (-not $Carpeta) { continue }
        $Ruta = Join-Path $Carpeta "cloudflared\cloudflared.exe"
        if (Test-Path $Ruta) { return $Ruta }
    }
    throw "No se encontró cloudflared. Instalalo con: winget install --id Cloudflare.cloudflared (o usá -Local para levantar la app sin túnel)."
}

function Abrir-Tunel([string]$Cloudflared) {
    Escribir-Paso "Abriendo el túnel de Cloudflare"
    $Log = Join-Path $env:TEMP "ecoharmony-tunel.log"
    Remove-Item $Log -ErrorAction SilentlyContinue
    $Proceso = Start-Process -FilePath $Cloudflared `
        -ArgumentList @("tunnel", "--no-autoupdate", "--url", "http://127.0.0.1:$Puerto") `
        -RedirectStandardError $Log -WindowStyle Hidden -PassThru
    for ($Intento = 0; $Intento -lt 60; $Intento++) {
        Start-Sleep -Seconds 1
        if ($Proceso.HasExited) { throw "cloudflared se cerró. Revisá el log: $Log" }
        $Coincidencia = Select-String -Path $Log -Pattern "https://[a-z0-9-]+\.trycloudflare\.com" -ErrorAction SilentlyContinue |
            Select-Object -First 1
        if ($Coincidencia) {
            return @{ Proceso = $Proceso; Url = $Coincidencia.Matches[0].Value }
        }
    }
    Stop-Process -Id $Proceso.Id -ErrorAction SilentlyContinue
    throw "El túnel no informó su link en 60 segundos. Revisá el log: $Log"
}

function Escribir-UrlPublica([string]$Url) {
    # Se reescribe solo la línea URL_PUBLICA, sin BOM, para que el resto del
    # .env (credenciales) quede igual.
    $Lineas = [System.Collections.Generic.List[string]][System.IO.File]::ReadAllLines($RutaEnv, $Utf8SinBom)
    $Indice = $Lineas.FindIndex([Predicate[string]]{ param($Linea) $Linea.StartsWith("URL_PUBLICA=") })
    if ($Indice -ge 0) { $Lineas[$Indice] = "URL_PUBLICA=$Url" } else { $Lineas.Add("URL_PUBLICA=$Url") }
    [System.IO.File]::WriteAllLines($RutaEnv, $Lineas, $Utf8SinBom)
}

Preparar-Entorno
Verificar-Env
Verificar-Puerto

$Tunel = $null
if ($Local) {
    $UrlPublica = "http://127.0.0.1:$Puerto/"
} else {
    $Tunel = Abrir-Tunel (Buscar-Cloudflared)
    $UrlPublica = "$($Tunel.Url)/"
}
Escribir-UrlPublica $UrlPublica

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " EcoHarmony Park está en: $UrlPublica" -ForegroundColor Cyan
if ($Tunel) {
    Set-Clipboard -Value $UrlPublica
    Write-Host " (link copiado al portapapeles; compartilo solo con el grupo)" -ForegroundColor Cyan
}
Write-Host " Ctrl+C para apagar la app$(if ($Tunel) { ' y el túnel' })." -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

try {
    & $PythonVenv -m uvicorn app.main:app --host 127.0.0.1 --port $Puerto --proxy-headers --forwarded-allow-ips 127.0.0.1
} finally {
    if ($Tunel -and -not $Tunel.Proceso.HasExited) {
        Stop-Process -Id $Tunel.Proceso.Id -ErrorAction SilentlyContinue
        Write-Host "Túnel apagado." -ForegroundColor Green
    }
}
