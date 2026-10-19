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
| Redirigir a Mercado Pago si se paga con tarjeta | puerto `pasarela_pago`, `PasarelaMercadoPago` (Checkout Pro) y botón del front | CP-24, CP-01, pruebas de `test_pasarela_mercado_pago.py` |
| Completar el pago con Mercado Pago | `ServicioCompra.confirmar_pago`, `PasarelaMercadoPago.consultar_pago` y `POST /compras/{id}/pago` | CP-29 a CP-34 |
| Enviar un mail de confirmación | puerto `notificador`, `NotificadorSMTP` y aviso en el front (FAQ 5). Con tarjeta, cuando Mercado Pago aprueba el pago | CP-25, CP-30, CP-01, pruebas de `test_notificador_smtp.py` |
| Informar la cantidad de entradas compradas y la fecha | `Compra.resumen()` | CP-26 |
| Solo usuarios registrados pueden comprar | `ServicioCompra` y cabecera `X-Usuario-Email` (sesión simulada, FAQ 19) | CP-07 |

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
  ├─ modelos.py         (SolicitudCompra, Compra, EstadoCompra, PagoInformado, TipoPase, MedioPago)
  ├─ calendario.py      (días de apertura y ventana de compra)
  ├─ precios.py         (precio base y descuentos por edad)
  └─ errores.py         (CompraInvalidaError, CompraNoEncontradaError, UsuarioNoRegistradoError, PagoNoDisponibleError)

adaptadores/            ← implementaciones de los puertos (reloj, repositorios SQLite y en memoria, mail SMTP, Mercado Pago)
dependencias.py         ← composición: elige los adaptadores según la configuración (.env)
static/                 ← front: index.html, styles.css y app.js, servidos por FastAPI en /
```

### Decisiones y justificación

1. **Reglas de negocio en funciones puras (`calendario.py`, `precios.py`).** Se prueban sin servidor ni base de datos, las pruebas son rápidas (129 pruebas en unos pocos segundos) y cada regla tiene un único lugar donde cambiarla.

2. **Servicio de aplicación (`ServicioCompra`) con inyección de dependencias.** El servicio recibe por constructor el reloj, los repositorios, el notificador y la pasarela de pago. Así, en las pruebas se reemplazan por dobles (`RelojFijo`, `NotificadorEnMemoria`, `MercadoPagoQueInforma` o la pasarela contra el Mercado Pago simulado) y en producción por los adaptadores reales. Esta decisión surgió de TDD: para escribir la prueba del mail (CP-25) hacía falta observar el envío sin mandar un mail real.

3. **Reloj inyectable.** Las reglas de fecha (día actual, 31 días, 17:30, feriados) dependen de "ahora". Con `datetime.now()` directo, las pruebas fallarían según el día en que se ejecuten. Con un reloj inyectado, cada prueba fija su propia fecha y hora; por ejemplo, para el 1 de enero y el 25 de diciembre se usa como "ahora" el 20/12/2026, así esas pruebas fallan por el feriado y no por superar los 31 días.

4. **Puertos para servicios externos (Mercado Pago y mail).** Se definieron interfaces mínimas (`crear_pago(compra) → url` y `enviar_confirmacion(compra)`). Al principio solo existían adaptadores simulados; la integración real se agregó después escribiendo adaptadores nuevos, sin tocar el dominio ni el servicio (ver decisiones 10 y 11).

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

10. **Mercado Pago Checkout Pro (`PasarelaMercadoPago`).** Crea una *preferencia* con un ítem por el total de la compra, `external_reference` con el id de la compra y `back_urls` que vuelven al front; devuelve el link de pago. Se usa la API REST con `httpx`, que ya estaba en el proyecto, en lugar del SDK de Mercado Pago, para no agregar una dependencia por una sola llamada.
    - Las pruebas reemplazan la red con `httpx.MockTransport`: verifican lo que se envía (token, total, moneda, referencia y URLs de retorno) sin credenciales ni conexión.
    - Con credenciales de prueba antiguas (`TEST-...`) devuelve el checkout de prueba (`sandbox_init_point`); con las demás, `init_point`. Las credenciales de prueba que Mercado Pago genera desde noviembre de 2025 empiezan con `APP_USR-` y funcionan con `init_point` y un comprador de prueba (probado con la cuenta de un integrante).
    - El título del ítem lleva la fecha con palabras ("20 de octubre de 2026"): Mercado Pago le quita las barras al título y "20/10/2026" se veía "20102026".
    - Si Mercado Pago rechaza la solicitud o no responde, se lanza `PagoNoDisponibleError` y la API responde **502** con un mensaje claro. La compra se anula (decisión 15).
    - Una compra con tarjeta de $0 (todos los visitantes de hasta 3 años) no se envía a Mercado Pago, que no acepta cobros de $0.
    - Si la URL pública es `https`, la preferencia pide `auto_return: approved` para que Mercado Pago vuelva solo al sitio al aprobarse el pago. Con la dirección local (`http://127.0.0.1`) no se pide, porque Mercado Pago puede rechazar la preferencia por esa URL; el usuario vuelve con el botón "Volver al sitio".

11. **Mail por SMTP (`NotificadorSMTP`).** Usa `smtplib` y `email.message` de la biblioteca estándar, con STARTTLS. El mail informa el número de compra, la cantidad de entradas, la fecha, el pase, el total y el pago: aprobado con Mercado Pago, en boletería o sin costo. Las pruebas reemplazan el servidor SMTP por uno falso. Si el envío falla, el error queda en el log y **la compra no falla**: ya está registrada, y un error en ese momento haría que el visitante crea que no compró y vuelva a intentarlo.

12. **Configuración por variables de entorno (`.env`).** `dependencias.py` lee `backend/.env` (con `python-dotenv`) y elige cada adaptador: si hay `MP_ACCESS_TOKEN` usa Mercado Pago real y si hay `SMTP_HOST`, el mail real; si no, las versiones simuladas. Así el proyecto funciona sin credenciales (por ejemplo, para corregirlo) y las credenciales nunca se suben al repositorio. Las funciones de selección reciben la configuración como diccionario, para probarlas sin depender del `.env` de cada integrante.

13. **Front sin framework, servido por FastAPI.** El FAQ del PO pide una web responsive (24), con su paleta y la fuente Lato (3), un calendario con los días cerrados deshabilitados (2), la redirección a Mercado Pago (4) y un aviso del mail enviado (5). Se resolvió con HTML, CSS y JavaScript sin herramientas de build, en el mismo servidor que la API.
    - Para no repetir reglas de negocio en JavaScript, el front las consulta al backend: `GET /fechas-disponibles` (fechas habilitadas en el calendario, calculadas con las mismas reglas que validan la compra) y `POST /cotizacion` (total antes de elegir la forma de pago, como describe el dominio).
    - El backend sigue validando todo al comprar: el front solo ayuda a no equivocarse.
    - Al volver de Mercado Pago, el front envía el id del pago al backend (`POST /compras/{id}/pago`), que lo verifica (decisión 14), y recién entonces informa el pago aprobado y el mail enviado.
    - El logo es provisorio: el FAQ 17 pide diseñarlo y validarlo con el PO.

14. **Estado de la compra y confirmación del pago.** La compra tiene un estado (`EstadoCompra`): en efectivo o sin costo queda **confirmada** y se envía el mail; con tarjeta queda **pendiente de pago** hasta que Mercado Pago lo aprueba.
    - Mercado Pago vuelve al sitio con `payment_id` y `external_reference` en la URL. El front los envía a `POST /compras/{id}/pago` y el servicio **consulta el pago a la API de Mercado Pago** (`GET /v1/payments/{id}`) en lugar de confiar en los datos de la URL, que cualquiera puede escribir a mano.
    - Se confirma solo si el pago está aprobado, corresponde a esa compra (`external_reference`) y es por el total. Una compra de otro usuario responde 404, como si no existiera.
    - Confirmar es idempotente: si la compra ya está confirmada (por ejemplo, el usuario recarga la página), no se consulta otra vez ni se reenvía el mail.
    - Un id de pago que no es numérico no se consulta, para no armar la URL de la API de Mercado Pago con texto arbitrario recibido del front.
    - Sin credenciales se usa el Mercado Pago simulado (decisión 17), así que el flujo se puede probar sin cuenta de Mercado Pago.
    - **No se implementó el webhook** (notificaciones IPN) de Mercado Pago: necesita una URL pública a la que Mercado Pago pueda llamar, que no existe en el entorno local. La consecuencia es que, si el usuario paga y cierra la pestaña sin volver al sitio, la compra queda pendiente. Con una URL pública, el webhook podría llamar al mismo `ServicioCompra.confirmar_pago`.

15. **Si Mercado Pago no está disponible, la compra se anula.** Para tener el id que se envía como `external_reference`, la compra se registra antes de crear el pago. Si después Mercado Pago no responde, la compra queda **anulada**: no cuenta para el límite de 10 entradas por fecha (FAQ 27) y no se puede confirmar su pago. Antes de este cambio quedaba registrada sin link de pago y bloqueaba entradas del usuario.

16. **Fechas de las pruebas calculadas a partir del día actual.** Las pruebas no usan fechas fijas (`tests/fechas.py`): una fecha fija termina quedando en el pasado o fuera de la ventana de 31 días y la prueba falla con el paso del tiempo, aunque el sistema no haya cambiado. Cada fecha se busca a partir de hoy según lo que necesita la prueba (el próximo lunes, el próximo 25 de diciembre, una fecha de visita abierta, etc.). Los días de apertura se escriben en ese módulo a partir del FAQ 1, sin usar el código de la aplicación, para no elegir los datos de prueba con la misma lógica que se prueba. Las reglas de fecha siguen recibiendo "ahora" por el reloj inyectado (decisión 3).

17. **Mercado Pago simulado cuando no hay credenciales.** Sin `MP_ACCESS_TOKEN`, la aplicación usa un Mercado Pago simulado en memoria (`app/mercado_pago_simulado/`), con el mismo contrato que la API real: crear la preferencia, consultar un pago y buscar pagos. `PasarelaMercadoPago` es la misma clase en los dos modos y solo cambia la URL de la API (`url_api`). En modo simulado le habla al simulador con un transporte de `httpx` dentro del mismo proceso, que solo atiende `/mercadopago-simulado/api`. El titular de la tarjeta define el resultado, como con las tarjetas de prueba reales (`APRO` aprueba, `OTHE` rechaza, `CONT` deja pendiente). El diseño está en [docs/diseno-mercado-pago-simulado.md](docs/diseno-mercado-pago-simulado.md). La página de checkout simulada quedó mínima: el grupo priorizó la integración real en modo prueba.

18. **El pago se hace en otra pestaña y el sitio lo verifica por el número de compra.** Mercado Pago solo vuelve solo al sitio (`auto_return`) si la URL de vuelta es pública y `https`. Con `http://127.0.0.1` o `http://localhost` la API respondió `400 auto_return invalid. back_url.success must be defined` (probado con las credenciales de prueba del grupo), y la pantalla de pago aprobado no muestra un botón para volver.
    - El botón "Pagar con Mercado Pago" abre el checkout en una pestaña nueva, y la pestaña del sitio muestra "Esperando tu pago en Mercado Pago…".
    - Mientras espera, la pestaña del sitio llama a `POST /compras/{id}/verificacion-de-pago` cada 5 segundos y cuando el usuario vuelve a mirarla.
    - Ese endpoint usa `ServicioCompra.verificar_pago`, que busca los pagos de la compra en Mercado Pago (`GET /v1/payments/search?external_reference=<compra>`) y aplica las mismas reglas que `confirmar_pago`: pago de esa compra, por el total y aprobado. Entonces confirma la compra y envía el mail una sola vez.
    - La respuesta informa el pago como `aprobado`, `rechazado`, `pendiente` o `sin_pago`, y el front muestra "¡Pago aprobado!" con la cantidad de entradas y la fecha (criterio de aceptación) o el rechazo.
    - Se conserva la confirmación por la URL de vuelta (`POST /compras/{id}/pago`), por si se publica la aplicación en `https`.
    - La compra que espera el pago se guarda en el navegador (`localStorage`, junto con el email de la sesión). Si la pestaña del sitio se recarga o se cierra después de pagar, al abrir el sitio de nuevo con la misma sesión la compra se vuelve a verificar. Así se cubre en parte el caso de la decisión 14. Si el usuario nunca vuelve a abrir el sitio en ese navegador, la compra queda pendiente: solo un webhook, que necesita una URL pública, lo resolvería del todo.
    - Cada compra con tarjeta tiene una **referencia de pago única** (`referencia_pago`, un uuid guardado en la base), que se usa como `external_reference`. El número de compra no sirve: se repite si se borra la base o si otro integrante usa las mismas credenciales, y un pago ajeno con el mismo número y el mismo total confirmaba la compra (hallazgo de la revisión final). Las compras con tarjeta registradas antes de este cambio usan su número.
    - Confirmar o verificar un pago se hace de a una solicitud por vez (`threading.Lock` en `ServicioCompra`): dos consultas simultáneas (el intervalo y `visibilitychange`) enviaban el mail dos veces.

## 4. Reglas definidas por el PO y supuestos

Las respuestas del FAQ del PO ([FAQ_PO.md](FAQ_PO.md)) definen la mayoría de los valores. Lo que ni el enunciado ni el FAQ definen se resolvió con supuestos explícitos. Todos los valores están en constantes fáciles de modificar:

| Regla | Valor | Origen | Ubicación |
|---|---|---|---|
| Precio base del pase regular | $10.000 | FAQ 6 | `dominio/precios.py` |
| Precio base del pase VIP | $20.000 | FAQ 6 | `dominio/precios.py` |
| Descuentos por edad | Hasta 3 años gratis; hasta 15 y desde 60 años, 50 % | FAQ 7 | `dominio/precios.py` |
| Los descuentos por edad aplican a ambos tipos de pase | Sí (el VIP solo cambia el precio) | Supuesto, apoyado en el FAQ 21 | `dominio/precios.py` |
| Días de cierre | Lunes, 1 de enero y 25 de diciembre | FAQ 1 | `dominio/calendario.py` |
| Anticipación máxima | 31 días (el día 31 se acepta, el 32 no) | Supuesto: el FAQ 25 dice "no más de un mes" | `dominio/calendario.py` |
| Hora límite para comprar para el día actual | 17:30 inclusive (17:31 se rechaza) | FAQ 26 | `dominio/calendario.py` |
| Se debe informar una edad por cada entrada | `len(edades) == cantidad` (CP-27) | Supuesto | `ServicioCompra` |
| Límite de 10 entradas por usuario y fecha, sumando compras | Se cuentan las compras confirmadas y pendientes de pago, no las anuladas | FAQ 27 | `ServicioCompra`, `entradas_compradas()` |
| Momento del mail de confirmación | En efectivo o sin costo, al registrar la compra; con tarjeta, cuando Mercado Pago aprueba el pago | Decisión del grupo (FAQ 5: "Desarrollo") | `ServicioCompra` |
| Compra con tarjeta de $0 | No se redirige a Mercado Pago y se confirma | Supuesto | `ServicioCompra` |
| Sin máximo de visitantes por día | No se controla un cupo diario | FAQ 20 | — |

## 5. Diseño de las pruebas

- **Pirámide de pruebas:** la mayoría son **unitarias** del dominio, del servicio y de los adaptadores (`tests/unit/`); menos pruebas **de API** (`tests/test_api_compras.py`, `tests/test_api_front.py`) verifican el contrato HTTP (códigos, JSON, cabeceras), el flujo completo de CP-01 y que el front se sirva. El front (JavaScript) no tiene pruebas automatizadas: se probó a mano en el navegador, en escritorio y en celular.
- **Clases de equivalencia y valores límite:** cada regla se prueba en sus bordes, por ejemplo cantidad 0, -1, 1, 10 y 11; edades 0, 3, 4, 15, 16, 59 y 60; fechas a 31 y 32 días; horas 17:30 y 17:31.
- **Una razón de fallo por prueba:** los helpers `solicitud()` / `solicitud_valida()` arman una solicitud válida y cada prueba cambia solo el dato que evalúa.
- **Trazabilidad:** el nombre o el id de cada prueba contiene el código del caso del `BACKLOG.md` (por ejemplo, `test_cp13_lunes_es_rechazado`, `[CP-08]`).
- **Patrón Arrange-Act-Assert** y fixtures de pytest (`conftest.py`) para reutilizar la configuración.
- **Fechas dinámicas:** ninguna prueba usa una fecha fija (decisión 16). Se verificó corriendo la batería completa con 124 "hoy" simulados distintos, entre ellos todos los días de diciembre y enero.
- **Cobertura:** 99 % de las sentencias de `app/` (129 pruebas). Los repositorios SQLite están cubiertos al 100 %. Las únicas líneas sin cubrir usan el reloj real (`datetime.now()` y `obtener_reloj()`, que las pruebas reemplazan por un reloj fijo) y la escritura en el log del mail simulado.

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

Ejemplo de compra en `http://127.0.0.1:8000/docs`, con la cabecera `X-Usuario-Email: visitante@ecoharmony.com` y una fecha de `GET /fechas-disponibles` (de hoy a 31 días, sin lunes ni feriados):

```json
{
  "fecha_visita": "AAAA-MM-DD",
  "cantidad": 2,
  "edades": [40, 8],
  "tipo_pase": "REGULAR",
  "medio_pago": "TARJETA"
}
```

1. `POST /compras` responde `201` con `id`, `total`, `url_pago` (Mercado Pago), `estado` (`PENDIENTE_DE_PAGO`) y `mensaje` ("Compraste 2 entradas para el DD/MM/AAAA").
2. Al volver de Mercado Pago, `POST /compras/{id}/pago` con `{"id_pago": "<payment_id de la URL de vuelta>"}` responde `200` con `estado` `CONFIRMADA`, y se envía el mail de confirmación.
