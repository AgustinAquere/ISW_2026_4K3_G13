# TP 06 - Desarrollo guiado por pruebas (TDD)

## Sistema de compra de entradas

Trabajo práctico grupal de Ingeniería y calidad de software (UTN FRC).

El objetivo es desarrollar un sistema de compra de entradas para un parque, aplicando la metodología **Test-Driven Development (TDD)**.

## Tecnologías

- **Backend:** Python 3.12+ y FastAPI.
- **Persistencia:** SQLite (`sqlite3` de la biblioteca estándar). La base `backend/ecoharmony.db` se crea sola al iniciar la aplicación y está excluida del repositorio. Las pruebas usan repositorios en memoria o una base SQLite `:memory:`.
- **Testing:** pytest, HTTPX y pytest-cov.
- **Estilo de código:** PEP 8, verificado con Ruff (`backend/pyproject.toml`).

## Estructura del proyecto

- `backend/app/dominio/`: reglas de negocio puras (calendario del parque, precios y descuentos, modelos).
- `backend/app/servicios/`: caso de uso de compra de entradas.
- `backend/app/adaptadores/`: reloj, repositorios SQLite y en memoria, mail y Mercado Pago simulados.
- `backend/app/routers/`: endpoints HTTP.
- `backend/tests/unit/`: pruebas unitarias del dominio y del servicio.
- `backend/tests/`: pruebas de la API.
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

## Ejecutar la aplicación

Con el entorno virtual activado (en Windows y en Linux):

```bash
uvicorn app.main:app --reload
```

La API estará disponible en `http://127.0.0.1:8000`. La documentación interactiva se encuentra en `http://127.0.0.1:8000/docs`. Para detener el servidor: `Ctrl+C`.

Para comprar entradas (`POST /compras`) se debe enviar la cabecera `X-Usuario-Email: visitante@ecoharmony.com`, que simula la sesión de un usuario registrado.

Ejemplo desde una terminal de Linux con `curl`:

```bash
curl -X POST http://127.0.0.1:8000/compras \
  -H "Content-Type: application/json" \
  -H "X-Usuario-Email: visitante@ecoharmony.com" \
  -d '{"fecha_visita": "2026-11-15", "cantidad": 2, "edades": [40, 8], "tipo_pase": "REGULAR", "medio_pago": "TARJETA"}'
```

La fecha de visita debe estar entre hoy y los próximos 31 días, y no puede ser lunes.

## Ejecutar las pruebas

Con el entorno virtual activado (en Windows y en Linux):

```bash
pytest --cov=app
ruff check app tests
```

## Metodología de trabajo

Se aplicará TDD siguiendo el ciclo:

1. **Red:** escribir una prueba que falle.
2. **Green:** implementar el mínimo código necesario para que pase.
3. **Refactor:** mejorar el código manteniendo las pruebas aprobadas.

Las funcionalidades se desarrollarán de forma incremental y se validarán mediante pruebas automatizadas.
