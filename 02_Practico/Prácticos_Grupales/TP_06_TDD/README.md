# TP 06 - Desarrollo guiado por pruebas (TDD)

## Sistema de compra de entradas

Trabajo práctico grupal de Ingeniería y calidad de software (UTN FRC).

El objetivo es desarrollar un sistema de compra de entradas para un parque, aplicando la metodología **Test-Driven Development (TDD)**.

## Tecnologías

- **Backend:** Python, FastAPI y SQLAlchemy.
- **Base de datos:** SQLite.
- **Testing:** pytest y HTTPX.
- **Frontend:** HTML, CSS y JavaScript.

## Estructura del proyecto

- `backend/app/`: aplicación y lógica del backend.
- `backend/tests/`: pruebas automatizadas.
- `frontend/`: interfaz de usuario.

## Configuración del backend

Desde la carpeta `backend`, crear y activar un entorno virtual:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Instalar las dependencias:

```powershell
pip install -r requirements.txt
```

## Ejecutar la aplicación

Desde `backend`, ejecutar:

```powershell
uvicorn app.main:app --reload
```

La API estará disponible en `http://127.0.0.1:8000`. La documentación interactiva se encuentra en `http://127.0.0.1:8000/docs`.

## Ejecutar las pruebas

Desde `backend`:

```powershell
pytest
```

## Metodología de trabajo

Se aplicará TDD siguiendo el ciclo:

1. **Red:** escribir una prueba que falle.
2. **Green:** implementar el mínimo código necesario para que pase.
3. **Refactor:** mejorar el código manteniendo las pruebas aprobadas.

Las funcionalidades se desarrollarán de forma incremental y se validarán mediante pruebas automatizadas.
