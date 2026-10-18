# Decisiones de diseño — HU-01 Comprar entradas

Trabajo Práctico 6 — TDD · Ingeniería y Calidad de Software · UTN FRC · 4K3 · Grupo 13

## 1. User Story implementada

**Comprar entradas** (8 SP) — *COMO visitante QUIERO comprar una entrada PARA asegurar mi visita al parque.*

Criterios de aceptación cubiertos:

| Criterio | Dónde se implementa | Pruebas |
|---|---|---|
| Indicar fecha, cantidad, edad de cada visitante y tipo de pase (VIP o regular) | `schemas.CompraRequest` | CP-02 a CP-06, CP-27 |
| La fecha puede ser el día actual o futura | `dominio/calendario.py` | CP-12, CP-17 |
| La fecha debe estar dentro de los días en que el parque abre | `dominio/calendario.py` | CP-13 a CP-16 |
| La cantidad no puede superar las 10 entradas, por compra y por usuario y fecha sumando compras (FAQ 27 del PO) | `ServicioCompra` y `entradas_compradas()` de los repositorios | CP-08 a CP-11, CP-28 |
| Seleccionar la forma de pago: efectivo (boletería) o tarjeta | `MedioPago`, `ServicioCompra` | CP-02, CP-23 |
| Redirigir a Mercado Pago si se paga con tarjeta | puerto `pasarela_pago` | CP-24, CP-01 |
| Enviar un mail de confirmación | puerto `notificador` | CP-25, CP-01 |
| Informar la cantidad de entradas compradas y la fecha | `Compra.resumen()` | CP-26 |
| Solo usuarios registrados pueden comprar | `ServicioCompra` y cabecera `X-Usuario-Email` | CP-07 |

Las cuatro pruebas de usuario de la tarjeta están automatizadas: CP-01 (pasa), CP-02 (falla sin forma de pago), CP-13/14/15 (fallan con el parque cerrado) y CP-10 (falla con más de 10 entradas).

## 2. Tecnología y reglas de estilo

- **Lenguaje:** Python 3.12+ con **FastAPI** (API REST) y **Pydantic** (validación de datos de entrada).
- **Pruebas:** **pytest** con `TestClient` de FastAPI; cobertura medida con `pytest-cov`.
- **Estilo de código:** **PEP 8**, verificado automáticamente con **Ruff** (configuración en `backend/pyproject.toml`):
  - Líneas de 79 caracteres como máximo, indentación de 4 espacios.
  - `snake_case` para funciones y variables, `PascalCase` para clases y `MAYUSCULAS` para constantes (`pep8-naming`).
  - Imports ordenados: biblioteca estándar, terceros y módulos propios (`isort`).
  - Reglas `flake8-bugbear` (por ejemplo, encadenar excepciones con `raise ... from`).
  - Nombres del dominio en español, el mismo idioma de la User Story, para que el código use el vocabulario del negocio.
- **Formato:** `ruff format`, para que el estilo no dependa de quién escribe el código.

## 3. Arquitectura

Se separó el código en capas, con dependencias que apuntan siempre hacia el dominio:

```
routers/compras.py      ← HTTP: traduce JSON/cabeceras ⇄ objetos del dominio y errores ⇄ códigos HTTP
        │
servicios/compra_service.py   ← caso de uso "comprar": orquesta validaciones, cálculo, registro, pago y mail
        │
dominio/                ← reglas de negocio puras, sin FastAPI ni E/S
  ├─ modelos.py         (SolicitudCompra, Compra, TipoPase, MedioPago)
  ├─ calendario.py      (días de apertura y ventana de compra)
  ├─ precios.py         (precio base y descuentos por edad)
  └─ errores.py         (CompraInvalidaError, UsuarioNoRegistradoError)

adaptadores/            ← implementaciones de los puertos (reloj, repositorios SQLite y en memoria, mail, Mercado Pago)
dependencias.py         ← composición: arma el servicio con los adaptadores reales
```

### Decisiones y justificación

1. **Reglas de negocio en funciones puras (`calendario.py`, `precios.py`).** Se prueban sin servidor ni base de datos, las pruebas son rápidas (68 pruebas en ~0,3 s) y cada regla tiene un único lugar donde cambiarla.

2. **Servicio de aplicación (`ServicioCompra`) con inyección de dependencias.** El servicio recibe por constructor el reloj, los repositorios, el notificador y la pasarela de pago. Así, en las pruebas se reemplazan por dobles (`RelojFijo`, `NotificadorEnMemoria`, `PasarelaMercadoPagoSimulada`) y en producción por los adaptadores reales. Esta decisión surgió de TDD: para escribir la prueba del mail (CP-25) hacía falta observar el envío sin mandar un mail real.

3. **Reloj inyectable.** Las reglas de fecha (día actual, 31 días, 17:30, feriados) dependen de "ahora". Con `datetime.now()` directo, las pruebas fallarían según el día en que se ejecuten. Con un reloj inyectado, cada prueba fija su propia fecha y hora; por ejemplo, para el 1 de enero y el 25 de diciembre se usa como "ahora" el 20/12/2026, así esas pruebas fallan por el feriado y no por superar los 31 días.

4. **Puertos para servicios externos (Mercado Pago y mail).** La integración real con Mercado Pago y con un servidor SMTP excede la User Story y no se puede probar de forma automatizada y repetible. Se definieron interfaces mínimas (`crear_pago(compra) → url` y `enviar_confirmacion(compra)`) con adaptadores simulados. Cambiar a la integración real implica escribir un adaptador nuevo sin tocar el dominio ni el servicio.

5. **Persistencia con SQLite detrás de repositorios.** La aplicación guarda usuarios y compras en `backend/ecoharmony.db` mediante `RepositorioUsuariosSQLite` y `RepositorioComprasSQLite` (`adaptadores/repositorios_sqlite.py`). Tienen la misma interfaz que los repositorios en memoria (`guardar`, `obtener`, `listar`, `entradas_compradas`, `esta_registrado`), así que el cambio solo tocó `dependencias.py`: el dominio, el servicio y las pruebas existentes quedaron igual.
   - Se usa `sqlite3` de la biblioteca estándar en lugar de un ORM como SQLAlchemy: son dos tablas y cuatro consultas, y no hace falta agregar dependencias.
   - Las tablas se crean al construir cada repositorio (`CREATE TABLE IF NOT EXISTS`) y el usuario de demostración se carga con `INSERT OR IGNORE`, así que reiniciar el servidor no duplica datos.
   - Las edades se guardan como una lista JSON en una columna, porque siempre se leen junto con su compra.
   - `url_pago` no se guarda: Mercado Pago la genera después de registrar la compra, a partir de su id.
   - Los repositorios en memoria se mantienen como dobles de prueba para que la batería del servicio siga siendo rápida. Los de SQLite tienen sus propias pruebas sobre una base `:memory:` y una sobre un archivo temporal que verifica que los datos persisten al reabrir la base.

6. **Dos niveles de validación.**
   - *Estructural* (campos obligatorios, tipos, valores de `TipoPase`/`MedioPago`): lo resuelve Pydantic en el esquema y responde **422**.
   - *De negocio* (cantidad, edades, fecha): la valida el dominio y responde **400** con un mensaje que explica el motivo.
   - *Usuario no autenticado o no registrado:* responde **401**.

   Separar los niveles evita duplicar validaciones y deja las reglas del negocio fuera de la capa HTTP.

7. **Enumeraciones para tipo de pase y medio de pago.** Evitan cadenas mágicas: un valor inexistente (por ejemplo, `"COMUN"`) se rechaza en la entrada y el resto del código trabaja con valores válidos.

8. **Autenticación simulada con la cabecera `X-Usuario-Email`.** El registro y el inicio de sesión pertenecen a otra User Story. Para respetar el criterio "solo usuarios registrados", el servicio verifica que el email exista en el repositorio de usuarios; la cabecera representa la sesión iniciada. Más adelante se puede reemplazar por un token (JWT) sin cambiar el servicio.

9. **El mail se envía y la compra se registra solo si la compra es válida.** Primero se valida todo y después se producen los efectos (guardar, crear pago, enviar mail). Hay una prueba específica que verifica que una compra rechazada no deja registros ni envía mails.

## 4. Supuestos

Lo que el enunciado o la User Story no definen se resolvió con supuestos explícitos, ubicados en constantes fáciles de modificar:

| Supuesto | Valor | Ubicación |
|---|---|---|
| Precio base del pase regular | $10.000 | `dominio/precios.py` |
| Precio base del pase VIP | $20.000 | `dominio/precios.py` |
| Los descuentos por edad aplican a ambos tipos de pase | Sí | `dominio/precios.py` |
| Días de cierre | Lunes, 1 de enero y 25 de diciembre | `dominio/calendario.py` |
| Anticipación máxima | 31 días (el día 31 se acepta, el 32 no) | `dominio/calendario.py` |
| Hora límite para comprar para el día actual | 17:30 inclusive (17:31 se rechaza) | `dominio/calendario.py` |
| Se debe informar una edad por cada entrada | `len(edades) == cantidad` (CP-27, agregado) | `ServicioCompra` |
| Límite de 10 entradas por usuario y fecha, sumando compras | Confirmado por el PO (FAQ 27). Se controlan las compras registradas, sin importar el medio de pago | `ServicioCompra`, `entradas_compradas()` |
| Momento del mail de confirmación | Al registrar la compra, en ambos medios de pago | `ServicioCompra` |

Pendiente de validar con el PO: con tarjeta, ¿el mail se envía al registrar la compra o cuando Mercado Pago confirma el pago? Para la segunda opción haría falta un endpoint de notificación (webhook) de Mercado Pago, fuera del alcance de esta User Story.

## 5. Diseño de las pruebas

- **Pirámide de pruebas:** la mayoría son **unitarias** del dominio y del servicio (`tests/unit/`); menos pruebas **de API** (`tests/test_api_compras.py`) verifican el contrato HTTP (códigos, JSON, cabeceras) y el flujo completo de CP-01.
- **Clases de equivalencia y valores límite:** cada regla se prueba en sus bordes, por ejemplo cantidad 0, -1, 1, 10 y 11; edades 0, 3, 4, 15, 16, 59 y 60; fechas a 31 y 32 días; horas 17:30 y 17:31.
- **Una razón de fallo por prueba:** los helpers `solicitud()` / `solicitud_valida()` arman una solicitud válida y cada prueba cambia solo el dato que evalúa.
- **Trazabilidad:** el nombre o el id de cada prueba contiene el código del caso del `BACKLOG.md` (por ejemplo, `test_cp13_lunes_es_rechazado`, `[CP-08]`).
- **Patrón Arrange-Act-Assert** y fixtures de pytest (`conftest.py`) para reutilizar la configuración.
- **Cobertura:** 99 % de las sentencias de `app/`. Los repositorios SQLite están cubiertos al 100 %. Las únicas líneas sin cubrir son `datetime.now()` y la escritura en el log de los adaptadores reales.

El registro de los ciclos Red-Green-Refactor y la verificación de las pruebas mediante mutaciones están en [CICLO_TDD.md](CICLO_TDD.md).

## 6. Cómo ejecutar

Desde `backend/`, en Windows (las instrucciones para Linux/WSL están en el [README](README.md)):

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest --cov=app            # pruebas y cobertura
ruff check app tests        # reglas de estilo
uvicorn app.main:app --reload
```

Ejemplo de compra en `http://127.0.0.1:8000/docs`, con la cabecera `X-Usuario-Email: visitante@ecoharmony.com`:

```json
{
  "fecha_visita": "2026-11-15",
  "cantidad": 2,
  "edades": [40, 8],
  "tipo_pase": "REGULAR",
  "medio_pago": "TARJETA"
}
```

Respuesta `201`: `id`, `total`, `url_pago` (Mercado Pago) y `mensaje` ("Compraste 2 entradas para el 15/11/2026").
