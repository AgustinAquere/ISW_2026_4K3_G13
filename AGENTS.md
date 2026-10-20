# Instrucciones para agentes

Repositorio del Grupo 13 (4K3) de Ingeniería y Calidad de Software, UTN FRC, 2026. El proyecto que se ejecuta es el **TP 6 (TDD): compra de entradas de EcoHarmony Park**, en `02_Practico/Prácticos_Grupales/TP_06_TDD/`. Tiene un backend FastAPI y un front servido por el mismo backend, ambos en `backend/`. El resto del repo son documentos de la materia.

Respondé en español.

## Levantar el proyecto (después de clonar y después de cada pull)

Todos los comandos se ejecutan desde `02_Practico/Prácticos_Grupales/TP_06_TDD/backend`.

1. **Python 3.12 o 3.13, versión normal.** En Windows, `py` puede elegir una versión experimental (`3.13t`) en la que falla la instalación de dependencias. Para ver las versiones instaladas: `py -0p`. Hay que crear el entorno con una versión explícita, por ejemplo `py -3.13`.
2. **Crear el entorno virtual,** solo si no existe:
   - Windows: `py -3.13 -m venv .venv`
   - Linux: `python3 -m venv .venv-linux`
3. **Instalar las dependencias SIEMPRE, aunque el entorno ya exista:**
   - Windows: `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`
   - Linux: `.venv-linux/bin/python -m pip install -r requirements.txt`

   `requirements.txt` fija versiones; por ejemplo, Ruff 0.17.1. Un entorno creado antes de un pull puede tener versiones viejas, y entonces `ruff check` marca errores que no son del código. No saltees este paso.
4. **Archivo `.env`:** si no existe, copiar `.env.example` como `.env`.
   - **Sin credenciales** la app funciona igual: usa un Mercado Pago simulado y escribe los mails en la consola.
   - **Con Mercado Pago de prueba o mails reales,** la persona completa sus propias credenciales siguiendo `../CONFIGURACION_CREDENCIALES.md`.
   - **Nunca** commitees `.env`, ni pidas o pegues credenciales en el chat.
5. **Verificar,** con el Python del entorno virtual. Los tres comandos tienen que terminar sin errores antes de seguir:
   - `python -m pytest`: todas las pruebas pasan.
   - `python -m ruff check app tests`: sin errores.
   - `python -m ruff format --check app tests`: sin cambios.
6. **Levantar la app:**
   - Comando: `python -m uvicorn app.main:app --reload`.
   - Dirección: http://127.0.0.1:8000/.
   - Para comprar hay que ingresar con un email registrado, por ejemplo `visitante@ecoharmony.com`, o registrar uno con el botón "Registrarme".
   - Si hay SMTP configurado, comprar con `visitante@ecoharmony.com` envía un mail real a ese dominio, que es de un tercero. Para probar el mail conviene registrar un correo propio.

**Alternativa en Windows:**
- **`.\iniciar-demo.cmd -Local`:** hace los pasos 2, 3, 4 y 6 en un solo comando. Las dependencias las reinstala solo si cambió `requirements.txt`.
- **Sin `-Local`:** además publica la app en un link público con `cloudflared`. Usalo solo si la persona lo pide.

Más detalle en `02_Practico/Prácticos_Grupales/TP_06_TDD/README.md`.

## Al modificar el código

- **Estilo:** PEP 8, y PEP 257 para los docstrings. Las reglas están en `TP_06_TDD/REGLAS_DE_ESTILO.md`. `ruff check` y `ruff format --check` tienen que terminar sin errores.
- **TDD:** primero una prueba que falle (Red), después el código mínimo para que pase (Green) y por último el Refactor.
  - Las fechas de las pruebas son dinámicas: usar `tests/fechas.py`, nunca fechas fijas.
  - Cada caso de prueba se registra en `TP_06_TDD/BACKLOG.md` y cada ciclo en `TP_06_TDD/CICLO_TDD.md`.
- **Commits:**
  - Mensajes en español, con formato Conventional Commits: `test(...)` para el Red, `feat(...)` o `fix(...)` para el Green, `refactor(...)`, `docs(...)`.
  - No commitear directo a `main`: se trabaja en una rama y se abre un PR.
  - Merge con commit de merge, no squash, para conservar la evidencia de los ciclos TDD.
- **Fin de línea:** hay archivos con CRLF y otros con LF. Al editar, conservá el que tiene cada archivo.
