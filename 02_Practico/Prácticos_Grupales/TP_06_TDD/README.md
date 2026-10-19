# TP 06 - Desarrollo guiado por pruebas (TDD)

## Sistema de compra de entradas

Trabajo práctico grupal de Ingeniería y calidad de software (UTN FRC).

El objetivo es desarrollar un sistema de compra de entradas para un parque, aplicando la metodología **Test-Driven Development (TDD)**.

## Tecnologías

- **Backend:** Python 3.12+ y FastAPI.
- **Persistencia:** SQLite (`sqlite3` de la biblioteca estándar). La base `backend/ecoharmony.db` se crea sola al iniciar la aplicación y está excluida del repositorio. Las pruebas usan repositorios en memoria o una base SQLite `:memory:`.
- **Front:** HTML, CSS y JavaScript servidos por FastAPI en `http://127.0.0.1:8000`. Web responsive con la paleta y la fuente Lato indicadas por el PO; el calendario es [flatpickr](https://flatpickr.js.org/) (desde CDN).
- **Pagos:** Mercado Pago Checkout Pro (modo prueba) mediante su API REST.
- **Mail:** SMTP con `smtplib` de la biblioteca estándar.
- **Testing:** pytest, HTTPX y pytest-cov.
- **Estilo de código:** PEP 8, verificado con Ruff (`backend/pyproject.toml`).

## Estructura del proyecto

- `backend/app/dominio/`: reglas de negocio puras (calendario del parque, precios y descuentos, modelos).
- `backend/app/servicios/`: caso de uso de compra de entradas.
- `backend/app/adaptadores/`: reloj, repositorios SQLite y en memoria, Mercado Pago (real y simulado) y mail (SMTP y simulado).
- `backend/app/static/`: front de compra de entradas.
- `backend/app/routers/`: endpoints HTTP.
- `backend/tests/unit/`: pruebas unitarias del dominio y del servicio.
- `backend/tests/`: pruebas de la API.
- `CONSIGNA.md`: consigna del TP 6 y User Story asignada.
- `FAQ_PO.md`: respuestas del PO que aclaran el dominio (precios, días de cierre, límites).
- `CONFIGURACION_CREDENCIALES.md`: paso a paso para enviar mails reales y usar Mercado Pago en modo prueba.
- `BACKLOG.md`: casos de prueba y su estado.
- `DECISIONES_DE_DISENO.md`: justificación del diseño y supuestos.
- `CICLO_TDD.md`: registro de los ciclos Red-Green-Refactor y verificación de las pruebas (mutaciones).

## Configuración del backend

Requisito: Python 3.12 o superior. Todos los comandos se ejecutan desde la carpeta `backend`.

### Windows (PowerShell)

Crear y activar el entorno virtual, e instalar las dependencias:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Si `pip install` falla al compilar paquetes (`failed-wheel-build-for-install`), puede ser que `py` haya elegido una versión experimental de Python (por ejemplo, `3.13t`). Ver las versiones instaladas con `py -0p`, borrar la carpeta `.venv` y crearla con una versión normal: `py -3.13 -m venv .venv`.

### Linux / WSL

En Debian/Ubuntu puede ser necesario instalar antes el módulo de entornos virtuales:

```bash
sudo apt install python3-venv
```

Crear y activar el entorno virtual, e instalar las dependencias:

```bash
python3 -m venv .venv-linux
source .venv-linux/bin/activate
pip install -r requirements.txt
```

> Un entorno virtual creado en Windows no funciona en Linux, y viceversa. Si se trabaja sobre la misma carpeta desde Windows y desde WSL, se usan dos entornos: `.venv` para Windows y `.venv-linux` para Linux. Ambos están excluidos del repositorio en `.gitignore`.

En cada nueva terminal hay que volver a activar el entorno (`.\.venv\Scripts\Activate.ps1` en Windows, `source .venv-linux/bin/activate` en Linux). Para desactivarlo: `deactivate`.

### Credenciales de Mercado Pago y del mail

Copiar `backend/.env.example` como `backend/.env` y completarlo. El archivo `.env` está excluido del repositorio: **nunca subir credenciales**. El paso a paso completo (crear la cuenta de Gmail y la contraseña de aplicación, crear la aplicación de Mercado Pago y probar el flujo) está en [CONFIGURACION_CREDENCIALES.md](CONFIGURACION_CREDENCIALES.md).

- **Mercado Pago:** en el [panel de desarrolladores](https://www.mercadopago.com.ar/developers/panel/app), crear una aplicación de Checkout Pro y copiar el *Access Token* de las credenciales de prueba en `MP_ACCESS_TOKEN`. Para pagar se usan las [tarjetas de prueba](https://www.mercadopago.com.ar/developers/es/docs/checkout-pro/additional-content/your-integrations/test/cards) de Mercado Pago.
- **Mail:** completar `SMTP_HOST`, `SMTP_PUERTO`, `SMTP_USUARIO` y `SMTP_CONTRASENA`. Con Gmail: `smtp.gmail.com`, puerto `587` y una [contraseña de aplicación](https://myaccount.google.com/apppasswords) (no la contraseña de la cuenta).
- **Usuarios registrados:** `USUARIOS_REGISTRADOS` lista los emails que pueden comprar, separados por coma. Para recibir el mail de confirmación hay que ingresar en el front con uno de esos emails, y que sea una casilla real.

Si `MP_ACCESS_TOKEN` o `SMTP_HOST` quedan vacíos, la aplicación usa la versión simulada (lo indica en la consola al hacer la primera compra): el link de pago vuelve al sitio con el pago aprobado (FAQ 4) y el mail se escribe en el log.

## Demo con un link público (un solo comando, Windows)

Para que el grupo pruebe la app desde el navegador sin instalar nada, `backend/iniciar-demo.cmd` levanta la app en tu computadora y la publica en un link `https://….trycloudflare.com` con un túnel de Cloudflare.

Requisitos (una sola vez):
- Python 3.12 o 3.13.
- `cloudflared`: `winget install --id Cloudflare.cloudflared`.
- `backend/.env` completo, si se quiere usar Mercado Pago de prueba y mails reales ([CONFIGURACION_CREDENCIALES.md](CONFIGURACION_CREDENCIALES.md)). Si falta, el script lo copia de `.env.example` y la app usa el Mercado Pago simulado y escribe los mails en la consola.

Uso: doble clic en `backend/iniciar-demo.cmd`, o desde PowerShell en `backend`:

```powershell
.\iniciar-demo.cmd          # app + link público
.\iniciar-demo.cmd -Local   # solo http://127.0.0.1:8000/, sin túnel
```

Qué hace el script:
1. La primera vez crea `.venv` e instala las dependencias.
2. Abre el túnel y escribe el link en `URL_PUBLICA` del `.env` (con `https`, Mercado Pago vuelve solo al sitio después de pagar).
3. Levanta la app, muestra el link y lo copia al portapapeles.

`Ctrl+C` apaga la app y el túnel. El link cambia cada vez y funciona mientras la ventana esté abierta. Cualquiera que tenga el link puede usar la app (y hacer que envíe mails): compartilo solo con el grupo y apagalo al terminar.

## Ejecutar la aplicación

Con el entorno virtual activado (en Windows y en Linux):

```bash
uvicorn app.main:app --reload
```

El front de compra está en `http://127.0.0.1:8000`: se ingresa con un email registrado (sesión simulada, FAQ 19 del PO) y se completa la compra. La documentación interactiva de la API se encuentra en `http://127.0.0.1:8000/docs`. Para detener el servidor: `Ctrl+C`.

Para comprar entradas (`POST /compras`) se debe enviar la cabecera `X-Usuario-Email: visitante@ecoharmony.com`, que simula la sesión de un usuario registrado.

Ejemplo desde una terminal de Linux con `curl`:

```bash
curl -X POST http://127.0.0.1:8000/compras \
  -H "Content-Type: application/json" \
  -H "X-Usuario-Email: visitante@ecoharmony.com" \
  -d '{"fecha_visita": "AAAA-MM-DD", "cantidad": 2, "edades": [40, 8], "tipo_pase": "REGULAR", "medio_pago": "TARJETA"}'
```

La fecha de visita debe estar entre hoy y los próximos 31 días, y no puede ser lunes ni feriado de cierre: `GET /fechas-disponibles` lista las fechas válidas. Con tarjeta, la compra queda pendiente de pago y el checkout de Mercado Pago se abre en otra pestaña. La pestaña del sitio consulta `POST /compras/{id}/verificacion-de-pago` hasta que el pago se aprueba; recién entonces se confirma la compra y se envía el mail. Sin `MP_ACCESS_TOKEN`, la aplicación usa un Mercado Pago simulado (ver `DECISIONES_DE_DISENO.md`, decisiones 17 y 18).

## Ejecutar las pruebas

Con el entorno virtual activado (en Windows y en Linux):

```bash
pytest --cov=app
ruff check app tests
```

## Metodología de trabajo

Se aplicó TDD siguiendo el ciclo:

1. **Red:** escribir una prueba que falle.
2. **Green:** implementar el mínimo código necesario para que pase.
3. **Refactor:** mejorar el código manteniendo las pruebas aprobadas.

Las funcionalidades se desarrollaron de forma incremental y se validaron mediante pruebas automatizadas. El registro de cada ciclo está en [CICLO_TDD.md](CICLO_TDD.md), y desde el ciclo 7 los pasos se registran en commits separados (`Red: ...`, `Green: ...`, `Refactor: ...`); los ciclos 9 a 12 se agruparon en un solo commit Red y uno Green.
