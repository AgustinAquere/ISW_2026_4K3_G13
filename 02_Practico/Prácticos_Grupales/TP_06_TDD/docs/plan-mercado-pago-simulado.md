# Plan de implementación: Mercado Pago simulado

> **Para agentes:** SUB-SKILL REQUERIDO: usar superpowers:subagent-driven-development (recomendado) o superpowers:executing-plans para implementar este plan tarea por tarea. Los pasos usan casillas (`- [ ]`) para el seguimiento.

**Objetivo:** sin credenciales, la aplicación usa un Mercado Pago simulado con checkout, resultado según el titular y vuelta al sitio, para hacer la demo sin cuenta real.

**Arquitectura:**
- **Núcleo:** `MercadoPagoSimulado`, en memoria, guarda preferencias y pagos.
- **API:** una función atiende la API de Mercado Pago (`POST /checkout/preferences` y `GET /v1/payments/{id}`). La usan dos entradas: un transporte `httpx` en proceso, para `PasarelaMercadoPago`, y un router HTTP, para `/docs` y `curl`.
- **Checkout:** el router también sirve la página de checkout y recibe el pago del formulario.
- **Sin cambios:** `PasarelaMercadoPago` y `ServicioCompra` siguen igual. Solo se agrega la URL base de la API.

**Tecnologías:** Python 3.12+, FastAPI, Pydantic, httpx (`MockTransport`), pytest, Ruff. HTML, CSS y JS sin framework.

**Diseño:** [diseno-mercado-pago-simulado.md](diseno-mercado-pago-simulado.md). Leerlo antes de empezar.

## Restricciones globales

- Todos los comandos se corren desde `02_Practico/Prácticos_Grupales/TP_06_TDD/backend` con el entorno virtual activado.
- **TDD:** cada tarea es un ciclo con un commit por paso. Prefijos `Red: `, `Green: `, `Refactor: ` (solo si hubo refactor), `Front: ` y `Docs: `.
- **Commits:** mensajes en español y sin tildes en el asunto, como los anteriores. Cada mensaje termina con la línea `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. **No hacer push.**
- **Antes de cada commit:**
  - `pytest -q`: en un Red fallan solo las pruebas nuevas; en Green y Refactor pasan todas.
  - `ruff check app tests` y `ruff format --check app tests`: sin errores.
  - `git diff --cached --stat`: si un archivo aparece reescrito entero, es un cambio de fin de línea. Los archivos guardan CRLF y hay que conservarlo; ver la nota de CRLF en `CICLO_TDD.md` y el commit `04525ab`.
- **Pruebas sin fechas fijas:** si una prueba necesita una fecha, la toma de `tests/fechas.py`.
- **Sin dependencias nuevas:** `httpx`, `pydantic` y `fastapi` ya están en `requirements.txt`.
- **Tarjeta:** el número, el código y el vencimiento nunca salen del navegador. El backend del checkout recibe solo `titular`, `marca` (`visa`, `master` o `amex`) y `ultimos_digitos` (4 dígitos).
- **Aviso visible:** la página de checkout muestra siempre "Simulación · no se cobra dinero".
- **Token de simulación:** `TOKEN_SIMULADO = "SIMULADO"`. Prefijo de las rutas: `/mercadopago-simulado`.
- **Titular → resultado:**
  - `APRO` → `approved` / `accredited`
  - `CONT` → `pending` / `pending_contingency`
  - `OTHE` → `rejected` / `cc_rejected_other_reason`
  - `FUND` → `rejected` / `cc_rejected_insufficient_amount`
  - `SECU` → `rejected` / `cc_rejected_bad_filled_security_code`
  - cualquier otro → `rejected` / `cc_rejected_other_reason`

## Puntos de revisión

Casos que el diseño implica pero que ninguna prueba ejercitaría si no se agregan. Cada uno tiene su prueba en la tarea indicada:

1. **Titular en minúsculas o con espacios** (`" apro "`): debe dar `approved`, porque en la demo se escribe a mano. Prueba en la Tarea 1.
2. **Pagar dos veces una preferencia ya aprobada** (doble clic o "atrás" en el navegador): el segundo intento se rechaza (409) y no se crea otro pago. Pruebas en las Tareas 1 y 3.
3. **Un cuerpo de pago con el número de tarjeta**, por ejemplo un JS viejo o un `curl`: se rechaza con 422 y no se guarda nada. Prueba en la Tarea 3.
4. **Preferencia inexistente** (el servidor se reinició entre la compra y el pago): datos y pago responden 404 con un mensaje claro, no 500. Prueba en la Tarea 3.
5. **Confirmar con un id de pago que el simulador no conoce:** la API del sitio responde 502 con un mensaje de Mercado Pago, no 500. Prueba en la Tarea 4.

## Archivos

| Archivo | Responsabilidad |
|---|---|
| `app/mercado_pago_simulado/__init__.py` | Paquete (vacío) |
| `app/mercado_pago_simulado/nucleo.py` | `MercadoPagoSimulado`: preferencias, pagos, resultado por titular y URL de vuelta |
| `app/mercado_pago_simulado/api.py` | `responder_api` (contrato de la API de Mercado Pago) y `transporte_en_proceso` |
| `app/mercado_pago_simulado/router.py` | Rutas HTTP: API, página de checkout, datos de la preferencia y pago del formulario |
| `app/static/mercadopago-simulado/checkout.html`, `checkout.css`, `checkout.js`, `logo.svg` | Página de checkout |
| `app/adaptadores/pasarela_pago.py` | `PasarelaMercadoPago` recibe `url_api`; se borra `PasarelaMercadoPagoSimulada` |
| `app/dependencias.py` | `obtener_mercado_pago_simulado()` y `crear_pasarela_pago` usan el simulador sin credenciales |
| `app/main.py` | Incluir el router del simulador |
| `tests/unit/test_mercado_pago_simulado.py` | Pruebas del núcleo |
| `tests/unit/test_api_mercado_pago_simulado.py` | Pruebas del contrato de la API y de `PasarelaMercadoPago` contra el simulador |
| `tests/test_api_checkout_simulado.py` | Pruebas de las rutas del checkout |
| `tests/conftest.py`, `tests/test_api_compras.py`, `tests/test_dependencias.py`, `tests/unit/test_servicio_compra.py` | Migración al simulador nuevo |
| `tests/unit/test_pasarela_simulada.py` | Se borra |

---

### Tarea 1: núcleo del simulador (ciclo 19)

**Archivos:**
- Crear: `app/mercado_pago_simulado/__init__.py` y `app/mercado_pago_simulado/nucleo.py`
- Pruebas: `tests/unit/test_mercado_pago_simulado.py`

**Interfaces que produce:**
```python
TOKEN_SIMULADO = "SIMULADO"
RESULTADOS_POR_TITULAR: dict[str, tuple[str, str]]   # ver Restricciones globales
class PreferenciaInexistenteError(Exception): ...
class PreferenciaYaPagadaError(Exception): ...

class MercadoPagoSimulado:
    def __init__(self, url_publica: str) -> None
    def crear_preferencia(self, datos: dict) -> dict
    def obtener_preferencia(self, id_preferencia: str) -> dict | None
    def preferencias_creadas(self) -> list[dict]
    def total(self, id_preferencia: str) -> int
    def pagar(self, id_preferencia: str, titular: str, marca: str,
              ultimos_digitos: str) -> dict
    def obtener_pago(self, id_pago: int) -> dict | None
    def pagos_de_preferencia(self, id_preferencia: str) -> list[dict]
    def url_de_vuelta(self, id_pago: int) -> str
```

**Formato de los datos:**
- **Preferencia devuelta:** los `datos` recibidos (`items`, `external_reference`, `back_urls` y opcionalmente `auto_return`) más:
  - `id`: `"<COLLECTOR_ID>-<uuid4>"`, con `COLLECTOR_ID = "1234567890"`.
  - `init_point` y `sandbox_init_point`: los dos `f"{url_publica}mercadopago-simulado/checkout?pref_id={id}"`. `url_publica` se normaliza para terminar en `/`.
  - `date_created`.
- **Pago:**
  - `id`: un `int` correlativo, desde `1000000001`.
  - `status`, `status_detail`, `external_reference`.
  - `transaction_amount`: un `float`, igual a la suma de `unit_price * quantity` de los ítems.
  - `currency_id: "ARS"`, `payment_method_id` (la marca), `payment_type_id: "credit_card"`.
  - `card: {"last_four_digits": ...}`, `preference_id`, `merchant_order_id` (un `int` correlativo desde `2000000001`) y `date_created`.

- [ ] **Paso 1: escribir las pruebas que fallan**

Fixture `simulador = MercadoPagoSimulado("http://127.0.0.1:8000")` (sin barra final, a propósito). Helper `preferencia(simulador, **cambios)` con estos `datos`:
- `items=[{"title": "EcoHarmony Park", "quantity": 1, "unit_price": 15000, "currency_id": "ARS"}]`
- `external_reference="7"`
- `back_urls`: `success` → `http://sitio/ok`, `failure` → `http://sitio/mal`, `pending` → `http://sitio/pend`

```python
def test_la_preferencia_lleva_al_checkout_simulado(simulador):
    pref = preferencia(simulador)
    assert pref["init_point"] == (
        "http://127.0.0.1:8000/mercadopago-simulado/checkout"
        f"?pref_id={pref['id']}"
    )
    assert pref["sandbox_init_point"] == pref["init_point"]
    assert simulador.obtener_preferencia(pref["id"])["external_reference"] == "7"

def test_el_total_suma_precio_por_cantidad(simulador):
    pref = preferencia(simulador, items=[
        {"title": "a", "quantity": 2, "unit_price": 5000, "currency_id": "ARS"},
        {"title": "b", "quantity": 1, "unit_price": 3000, "currency_id": "ARS"}])
    assert simulador.total(pref["id"]) == 13000

@pytest.mark.parametrize("titular, estado, detalle", [
    ("APRO", "approved", "accredited"),
    ("CONT", "pending", "pending_contingency"),
    ("OTHE", "rejected", "cc_rejected_other_reason"),
    ("FUND", "rejected", "cc_rejected_insufficient_amount"),
    ("SECU", "rejected", "cc_rejected_bad_filled_security_code"),
    ("JUAN PEREZ", "rejected", "cc_rejected_other_reason"),
])
def test_el_titular_define_el_resultado(simulador, titular, estado, detalle):
    pago = simulador.pagar(preferencia(simulador)["id"], titular, "master", "0604")
    assert (pago["status"], pago["status_detail"]) == (estado, detalle)

def test_el_titular_se_compara_sin_mayusculas_ni_espacios(simulador):
    # Punto de revisión 1
    pago = simulador.pagar(preferencia(simulador)["id"], "  apro ", "visa", "3704")
    assert pago["status"] == "approved"

def test_el_pago_queda_registrado_con_el_monto_y_la_referencia(simulador):
    pref = preferencia(simulador)
    pago = simulador.pagar(pref["id"], "APRO", "master", "0604")
    assert simulador.obtener_pago(pago["id"]) == pago
    assert pago["transaction_amount"] == 15000
    assert pago["external_reference"] == "7"
    assert pago["card"] == {"last_four_digits": "0604"}
    assert pago["payment_type_id"] == "credit_card"

def test_los_ids_de_pago_son_numeros_correlativos(simulador):
    pref = preferencia(simulador)
    primero = simulador.pagar(pref["id"], "OTHE", "visa", "3704")
    segundo = simulador.pagar(pref["id"], "APRO", "visa", "3704")
    assert segundo["id"] == primero["id"] + 1
    assert simulador.pagos_de_preferencia(pref["id"]) == [primero, segundo]

def test_una_preferencia_aprobada_no_acepta_otro_pago(simulador):
    # Punto de revisión 2
    pref = preferencia(simulador)
    simulador.pagar(pref["id"], "APRO", "master", "0604")
    with pytest.raises(PreferenciaYaPagadaError):
        simulador.pagar(pref["id"], "APRO", "master", "0604")

def test_despues_de_un_rechazo_se_puede_volver_a_pagar(simulador):
    pref = preferencia(simulador)
    simulador.pagar(pref["id"], "OTHE", "master", "0604")
    assert simulador.pagar(pref["id"], "APRO", "master", "0604")["status"] == "approved"

def test_pagar_una_preferencia_inexistente_es_un_error(simulador):
    with pytest.raises(PreferenciaInexistenteError):
        simulador.pagar("no-existe", "APRO", "master", "0604")

@pytest.mark.parametrize("titular, back_url, estado", [
    ("APRO", "http://sitio/ok", "approved"),
    ("OTHE", "http://sitio/mal", "rejected"),
    ("CONT", "http://sitio/pend", "pending"),
])
def test_la_url_de_vuelta_usa_la_back_url_del_resultado(simulador, titular, back_url, estado):
    pref = preferencia(simulador)
    pago = simulador.pagar(pref["id"], titular, "master", "0604")
    url = simulador.url_de_vuelta(pago["id"])
    partes = urlsplit(url)
    parametros = parse_qs(partes.query)
    assert url.startswith(back_url + "?")
    assert parametros["payment_id"] == [str(pago["id"])]
    assert parametros["collection_id"] == [str(pago["id"])]
    assert parametros["status"] == parametros["collection_status"] == [estado]
    assert parametros["external_reference"] == ["7"]
    assert parametros["preference_id"] == [pref["id"]]
    assert parametros["payment_type"] == ["credit_card"]
    assert parametros["merchant_order_id"] == [str(pago["merchant_order_id"])]
    assert parametros["site_id"] == ["MLA"]
    assert parametros["processing_mode"] == ["aggregator"]

def test_preferencias_creadas_las_lista_en_orden(simulador):
    a, b = preferencia(simulador), preferencia(simulador, external_reference="8")
    assert [p["id"] for p in simulador.preferencias_creadas()] == [a["id"], b["id"]]
```

- [ ] **Paso 2: correrlas y ver que fallan.** `pytest tests/unit/test_mercado_pago_simulado.py -q`. Se espera un error de importación porque `app.mercado_pago_simulado` no existe. Commit `Red: nucleo del Mercado Pago simulado (ciclo 19)`.
- [ ] **Paso 3: implementar `nucleo.py`** con las interfaces de arriba.
  - Preferencias y pagos en diccionarios.
  - Normalizar el titular con `titular.strip().upper()`.
  - "Ya pagada" significa que existe un pago `approved` de esa preferencia.
  - `url_de_vuelta`: `success`, `failure` o `pending` según `status`, armada con `urlencode`.
- [ ] **Paso 4: correr la batería completa.** Tienen que pasar todas las pruebas. Commit `Green: nucleo del Mercado Pago simulado`. Si hubo refactor, un commit `Refactor: ...` aparte.

---

### Tarea 2: API simulada y `PasarelaMercadoPago` contra el simulador (ciclo 20)

**Archivos:**
- Crear: `app/mercado_pago_simulado/api.py`
- Modificar: `app/adaptadores/pasarela_pago.py` (constructor y uso de las URLs)
- Pruebas: `tests/unit/test_api_mercado_pago_simulado.py`

**Interfaces:**
- Usa de la Tarea 1: `MercadoPagoSimulado`, `TOKEN_SIMULADO`.
- Produce:
```python
def responder_api(simulador: MercadoPagoSimulado, metodo: str, camino: str,
                  autorizacion: str | None, cuerpo: dict | None) -> tuple[int, dict]
def transporte_en_proceso(simulador: MercadoPagoSimulado) -> httpx.MockTransport
PREFIJO_API_SIMULADA = "/mercadopago-simulado/api"

# pasarela_pago.py
URL_API_MERCADO_PAGO = "https://api.mercadopago.com"
URL_PREFERENCIAS_MERCADO_PAGO = f"{URL_API_MERCADO_PAGO}/checkout/preferences"  # se mantiene
URL_PAGOS_MERCADO_PAGO = f"{URL_API_MERCADO_PAGO}/v1/payments"                 # se mantiene
class PasarelaMercadoPago:
    def __init__(self, access_token, url_retorno, cliente=None,
                 url_api=URL_API_MERCADO_PAGO)
```

**Contrato de `responder_api`:**
- `camino` es relativo a la API, por ejemplo `/checkout/preferences` o `/v1/payments/1000000001`.
- `autorizacion` distinta de `f"Bearer {TOKEN_SIMULADO}"` → `(401, {"message": "invalid access token", "error": "unauthorized", "status": 401})`.
- `POST /checkout/preferences` → `(201, preferencia)`.
- `GET /v1/payments/{id}` → `(200, pago)`. Si no existe o el id no es numérico → `(404, {"message": "Payment not found", "error": "not_found", "status": 404})`.
- Cualquier otro camino → `404` con el mismo formato.
- `transporte_en_proceso` quita `PREFIJO_API_SIMULADA` del camino de `request.url.path` y llama a `responder_api`.

- [ ] **Paso 1: escribir las pruebas que fallan**

```python
URL_PUBLICA = "http://127.0.0.1:8000/"

def test_sin_token_la_api_responde_401(simulador):
    estado, cuerpo = responder_api(simulador, "GET", "/v1/payments/1", None, None)
    assert estado == 401 and cuerpo["status"] == 401

def test_con_otro_token_la_api_responde_401(simulador):
    estado, _ = responder_api(simulador, "POST", "/checkout/preferences",
                              "Bearer TEST-123", {"items": []})
    assert estado == 401

def test_un_pago_inexistente_responde_404(simulador):
    estado, cuerpo = responder_api(simulador, "GET", "/v1/payments/999",
                                   f"Bearer {TOKEN_SIMULADO}", None)
    assert estado == 404 and cuerpo["error"] == "not_found"

def pasarela_simulada(simulador):
    cliente = httpx.Client(transport=transporte_en_proceso(simulador))
    return PasarelaMercadoPago(TOKEN_SIMULADO, URL_PUBLICA, cliente,
                               url_api=f"{URL_PUBLICA.rstrip('/')}{PREFIJO_API_SIMULADA}")

def test_la_pasarela_crea_la_preferencia_en_el_simulador(simulador):
    url = pasarela_simulada(simulador).crear_pago(compra_con_tarjeta())  # total 15000, id 7
    (pref,) = simulador.preferencias_creadas()
    assert url == pref["init_point"]
    assert pref["external_reference"] == "7"
    assert simulador.total(pref["id"]) == 15000

def test_la_pasarela_informa_el_pago_aprobado_del_simulador(simulador):
    pasarela = pasarela_simulada(simulador)
    pasarela.crear_pago(compra_con_tarjeta())
    (pref,) = simulador.preferencias_creadas()
    pago = simulador.pagar(pref["id"], "APRO", "master", "0604")
    assert pasarela.consultar_pago(str(pago["id"])) == PagoInformado(str(pago["id"]), True, 7, 15000)

def test_la_pasarela_informa_el_pago_rechazado_del_simulador(simulador): ...  # OTHE → aprobado False

def test_un_pago_desconocido_por_el_simulador_es_pago_no_disponible(simulador):
    with pytest.raises(PagoNoDisponibleError):
        pasarela_simulada(simulador).consultar_pago("999")

def test_por_defecto_la_pasarela_usa_la_api_real():
    api = MercadoPagoFalso()   # reutilizar el de test_pasarela_mercado_pago.py
    PasarelaMercadoPago("TEST-1", URL_PUBLICA,
                        httpx.Client(transport=httpx.MockTransport(api))).crear_pago(compra_con_tarjeta())
    assert str(api.solicitudes[0].url) == "https://api.mercadopago.com/checkout/preferences"
```
`compra_con_tarjeta()` arma la compra con `FECHA_VISITA` de `tests/fechas.py`, `total=15000` e `id=7`. Para no duplicar dobles entre archivos, mover `MercadoPagoFalso` a `tests/conftest.py`.

- [ ] **Paso 2: correrlas y ver que fallan.** El error esperado es de importación de `app.mercado_pago_simulado.api`. Commit `Red: API del Mercado Pago simulado (ciclo 20)`.
- [ ] **Paso 3: implementar `api.py` y agregar `url_api` a `PasarelaMercadoPago`.** La pasarela usa `f"{self._url_api}/checkout/preferences"` y `f"{self._url_api}/v1/payments/{id_pago}"`. `crear_pago` sigue eligiendo `sandbox_init_point` solo si el token empieza con `TEST-`. Las pruebas existentes de `test_pasarela_mercado_pago.py` tienen que seguir pasando sin cambios.
- [ ] **Paso 4: batería completa, Ruff y commit** `Green: PasarelaMercadoPago contra el Mercado Pago simulado`.

---

### Tarea 3: rutas HTTP del simulador y del checkout (ciclo 21)

**Archivos:**
- Crear: `app/mercado_pago_simulado/router.py`
- Crear: `app/static/mercadopago-simulado/checkout.html`. Por ahora un HTML mínimo con el aviso y `<form id="form-tarjeta">`; el diseño completo llega en la Tarea 5.
- Modificar: `app/dependencias.py` (agregar `obtener_mercado_pago_simulado`) y `app/main.py` (incluir el router antes del `mount` de la carpeta estática)
- Pruebas: `tests/test_api_checkout_simulado.py`

**Interfaces:**
- Usa: `MercadoPagoSimulado` y sus errores (Tarea 1), y `responder_api` (Tarea 2).
- Produce:
```python
# dependencias.py
@lru_cache
def obtener_mercado_pago_simulado() -> MercadoPagoSimulado
    # url_publica = os.environ.get("URL_PUBLICA", URL_PUBLICA_POR_DEFECTO)

# router.py: router = APIRouter(prefix="/mercadopago-simulado")
GET|POST /api/{camino:path}            -> responder_api (Authorization desde la cabecera)
GET  /checkout                         -> FileResponse(app/static/mercadopago-simulado/checkout.html)
GET  /checkout/{id_preferencia}/datos  -> 200 {"descripcion": str, "total": int,
                                               "pagada": bool}; 404 si no existe
POST /checkout/{id_preferencia}/pagos  -> 201 {"pago": dict, "url_de_vuelta": str,
                                               "volver_automaticamente": bool}
    cuerpo: PagoCheckoutRequest(titular: str (no vacío), marca: Literal["visa","master","amex"],
            ultimos_digitos: str con patrón ^\d{4}$), model_config extra="forbid"
    404 {"detail": "Preferencia inexistente"}; 409 {"detail": "Este pago ya fue realizado"}
```
- `descripcion` es el `title` del primer ítem.
- `volver_automaticamente` es verdadero si la preferencia tiene `auto_return == "approved"` y el pago quedó `approved`.

- [ ] **Paso 1: escribir las pruebas que fallan**

El fixture `client` de `conftest.py` tiene que sobrescribir también `obtener_mercado_pago_simulado` con un simulador de prueba (`MercadoPagoSimulado("http://testserver/")`, fixture `mercado_pago_simulado`). Helper `crear_preferencia(simulador, auto_return=False)`.

```python
def test_la_pagina_de_checkout_se_sirve_con_el_aviso_de_simulacion(client):
    r = client.get("/mercadopago-simulado/checkout?pref_id=x")
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/html")
    assert "Simulación · no se cobra dinero" in r.text
    assert 'id="form-tarjeta"' in r.text

def test_los_datos_del_checkout_informan_descripcion_y_total(client, mercado_pago_simulado):
    pref = crear_preferencia(mercado_pago_simulado)
    r = client.get(f"/mercadopago-simulado/checkout/{pref['id']}/datos")
    assert r.json() == {"descripcion": "EcoHarmony Park", "total": 15000, "pagada": False}

def test_datos_de_una_preferencia_inexistente_responde_404(client):        # Punto de revisión 4
    assert client.get("/mercadopago-simulado/checkout/no-existe/datos").status_code == 404

def test_pagar_desde_el_checkout_devuelve_el_pago_y_la_url_de_vuelta(client, mercado_pago_simulado):
    pref = crear_preferencia(mercado_pago_simulado)
    r = client.post(f"/mercadopago-simulado/checkout/{pref['id']}/pagos",
                    json={"titular": "APRO", "marca": "master", "ultimos_digitos": "0604"})
    assert r.status_code == 201
    cuerpo = r.json()
    assert cuerpo["pago"]["status"] == "approved"
    assert cuerpo["url_de_vuelta"] == mercado_pago_simulado.url_de_vuelta(cuerpo["pago"]["id"])
    assert cuerpo["volver_automaticamente"] is False

def test_con_auto_return_un_pago_aprobado_vuelve_solo(client, mercado_pago_simulado): ...
    # auto_return="approved": True con APRO y False con OTHE

def test_pagar_una_preferencia_inexistente_responde_404(client):           # Punto de revisión 4
    r = client.post("/mercadopago-simulado/checkout/no-existe/pagos",
                    json={"titular": "APRO", "marca": "visa", "ultimos_digitos": "3704"})
    assert r.status_code == 404 and r.json()["detail"] == "Preferencia inexistente"

def test_pagar_dos_veces_una_preferencia_aprobada_responde_409(client, mercado_pago_simulado):  # Punto de revisión 2
    ...  # segundo POST → 409 y "Este pago ya fue realizado"; datos → "pagada": True

def test_el_numero_de_tarjeta_no_se_acepta_en_el_pago(client, mercado_pago_simulado):  # Punto de revisión 3
    pref = crear_preferencia(mercado_pago_simulado)
    r = client.post(f"/mercadopago-simulado/checkout/{pref['id']}/pagos",
                    json={"titular": "APRO", "marca": "master", "ultimos_digitos": "0604",
                          "numero": "5031755734530604"})
    assert r.status_code == 422
    assert mercado_pago_simulado.pagos_de_preferencia(pref["id"]) == []

@pytest.mark.parametrize("cambios", [{"marca": "naranja"}, {"ultimos_digitos": "06"},
                                     {"titular": ""}])
def test_datos_de_pago_invalidos_responden_422(client, mercado_pago_simulado, cambios): ...

def test_la_api_simulada_por_http_crea_y_consulta(client, mercado_pago_simulado):
    cab = {"Authorization": f"Bearer {TOKEN_SIMULADO}"}
    # DATOS_PREFERENCIA: los mismos datos que el helper preferencia() de la Tarea 1
    r = client.post("/mercadopago-simulado/api/checkout/preferences", headers=cab,
                    json=DATOS_PREFERENCIA)
    assert r.status_code == 201
    pago = mercado_pago_simulado.pagar(r.json()["id"], "APRO", "visa", "3704")
    assert client.get(f"/mercadopago-simulado/api/v1/payments/{pago['id']}",
                      headers=cab).json()["status"] == "approved"

def test_la_api_simulada_por_http_sin_token_responde_401(client):
    assert client.get("/mercadopago-simulado/api/v1/payments/1").status_code == 401
```
- [ ] **Paso 2: correrlas y ver que fallan.** Las rutas responden 404 o 405. Commit `Red: rutas del checkout simulado (ciclo 21)`.
- [ ] **Paso 3: implementar el router, `obtener_mercado_pago_simulado` y el `include_router` en `main.py`.** El `include_router` va antes del `app.mount("/", StaticFiles(...))`. Así `/mercadopago-simulado/checkout.js` y los demás archivos los sigue sirviendo la carpeta estática, y `/mercadopago-simulado/checkout` lo atiende la ruta.
- [ ] **Paso 4: batería completa, Ruff y commit** `Green: rutas del checkout simulado`.

---

### Tarea 4: la aplicación usa el simulador sin credenciales (ciclo 22)

**Archivos:**
- Modificar: `app/dependencias.py` (`crear_pasarela_pago`) y `app/adaptadores/pasarela_pago.py` (borrar `PasarelaMercadoPagoSimulada`)
- Modificar pruebas: `tests/conftest.py`, `tests/test_dependencias.py`, `tests/test_api_compras.py`, `tests/unit/test_servicio_compra.py`
- Borrar: `tests/unit/test_pasarela_simulada.py`

**Interfaces:**
- Usa: `obtener_mercado_pago_simulado` (Tarea 3), y `transporte_en_proceso` y `PREFIJO_API_SIMULADA` (Tarea 2).
- Produce:
```python
def crear_pasarela_pago(configuracion, simulador: MercadoPagoSimulado | None = None) -> PasarelaMercadoPago
    # sin MP_ACCESS_TOKEN: PasarelaMercadoPago(TOKEN_SIMULADO, url_retorno,
    #   httpx.Client(transport=transporte_en_proceso(simulador or obtener_mercado_pago_simulado())),
    #   url_api=f"{url_publica sin barra final}{PREFIJO_API_SIMULADA}")
    # conserva el aviso en el log: "Sin MP_ACCESS_TOKEN: se usa el Mercado Pago simulado"
```

- [ ] **Paso 1: migrar las pruebas y escribir las nuevas (Red).**
  - **`conftest.py`:**
    - El fixture `mercado_pago_simulado` (Tarea 3) se mantiene.
    - El fixture `pasarela_pago` pasa a construirse directamente: `PasarelaMercadoPago(TOKEN_SIMULADO, "http://testserver/", httpx.Client(transport=transporte_en_proceso(mercado_pago_simulado)), url_api="http://testserver" + PREFIJO_API_SIMULADA)`. Se arma directo, sin `crear_pasarela_pago`, para que el Red no rompa toda la batería.
  - **`test_servicio_compra.py`:** los tres usos de `pasarela_pago.pagos_creados` pasan a `mercado_pago_simulado.preferencias_creadas()`. En CP-24 se compara `[p["external_reference"] for p in ...] == [str(compra.id)]`.
  - **`test_dependencias.py`:** `test_sin_access_token_se_simula_mercado_pago` pasa a ser:
    ```python
    def test_sin_access_token_se_usa_el_mercado_pago_simulado():
        simulador = MercadoPagoSimulado("http://127.0.0.1:8000/")
        url = crear_pasarela_pago({}, simulador).crear_pago(compra_con_tarjeta())
        assert url.startswith("http://127.0.0.1:8000/mercadopago-simulado/checkout?pref_id=")
    ```
  - **`test_api_compras.py`:**
    - Helper `pagar_en_checkout(client, url_pago, titular) -> str`: lee `pref_id` de `url_pago`, hace `POST /mercadopago-simulado/checkout/{pref_id}/pagos` con `marca="master"` y `ultimos_digitos="0604"`, y devuelve `url_de_vuelta`.
    - `id_de_pago(url_de_vuelta)` se mantiene.
    - **CP-01:** compra con tarjeta → `url_pago.startswith("http://testserver/mercadopago-simulado/checkout?pref_id=")` → `pagar_en_checkout(..., "APRO")` → `POST /compras/{id}/pago` con `id_de_pago(url_de_vuelta)` → `CONFIRMADA` y un mail.
    - **Nueva CP-35** `test_cp35_pago_rechazado_en_el_checkout_deja_la_compra_pendiente_y_se_puede_reintentar`: con `OTHE`, confirmar → `PENDIENTE_DE_PAGO` y ningún mail. Después `APRO` sobre la misma preferencia y confirmar → `CONFIRMADA` y un mail.
    - **`test_confirmar_un_pago_que_no_corresponde_a_la_compra_responde_400`:** crear dos compras, pagar la segunda con `APRO` y confirmar la primera con ese pago → 400 y "no corresponde".
    - **Nueva** `test_confirmar_con_un_pago_inexistente_responde_502` (punto de revisión 5): `{"id_pago": "999"}` → 502 y `"Mercado Pago" in detail`.
    - El resto de las pruebas que usaban `id_de_pago(compra["url_pago"])` pasa por `pagar_en_checkout(..., "APRO")`.
  - **Borrar** `tests/unit/test_pasarela_simulada.py`.
- [ ] **Paso 2: correr la batería y ver el Red.**
  - **Falla** `test_sin_access_token_se_usa_el_mercado_pago_simulado`, con `TypeError` porque `crear_pasarela_pago` no recibe `simulador`. Es la regla nueva de este ciclo: la aplicación usa el simulador.
  - **Ya pasan** CP-01, CP-35 y las pruebas migradas, porque el `conftest` usa el simulador de las Tareas 1 a 3. Verifican que la migración de las pruebas está bien.
  - Commit `Red: la aplicacion usa el Mercado Pago simulado (ciclo 22)`. En el mensaje se explica qué falla y por qué el resto ya pasa.
- [ ] **Paso 3: implementar `crear_pasarela_pago` con el simulador** y borrar `PasarelaMercadoPagoSimulada` y sus importaciones. `grep -rn PasarelaMercadoPagoSimulada app tests` no tiene que devolver nada.
- [ ] **Paso 4: batería completa, Ruff y commit** `Green: la aplicacion usa el Mercado Pago simulado`.

---

### Tarea 5: página de checkout (front, sin TDD)

**Archivos:**
- Modificar: `app/static/mercadopago-simulado/checkout.html`
- Crear: `checkout.css`, `checkout.js` y `logo.svg` en la misma carpeta

**Qué tiene que tener (diseño, secciones 2.1 a 2.3, y los bocetos aprobados):**
- **Franja superior** `#009ee3` con el logo a la izquierda y el aviso "Simulación · no se cobra dinero" a la derecha, siempre visible. La fuente es la del sistema.
- **Formulario `#form-tarjeta`:** número, nombre del titular, vencimiento MM/AA, código, DNI y botón "Pagar $<total>". El total se formatea con `Intl.NumberFormat("es-AR", {style: "currency", currency: "ARS", maximumFractionDigits: 0})`.
- **Tarjeta de resumen:** descripción y total, tomados de `GET /checkout/{pref_id}/datos`.
- **Ayuda:** "Titular APRO = aprobado · OTHE = rechazado · CONT = pendiente".
- **Validación en el navegador** (diseño, 2.3):
  - Marca por prefijo y largo: Visa 4 (13, 16 o 19), Mastercard 51-55 o 2221-2720 (16), Amex 34 o 37 (15).
  - Luhn.
  - Código: 4 dígitos para Amex y 3 para las demás.
  - Vencimiento MM/AA con un mes futuro, calculado con `new Date()`.
  - DNI de 7 u 8 dígitos y titular obligatorio.
  - Mensajes junto al campo: "Revisá el número de tarjeta", etc.
- **Al pagar:** `POST .../pagos` con **solo** `titular`, `marca` y `ultimos_digitos`. Después, pantalla de resultado:
  - **approved:** tilde verde, "¡Listo! Se acreditó tu pago", monto, "Operación n.º <id>" y "Volver al sitio". Si `volver_automaticamente`, vuelve sola a los 5 s.
  - **rejected:** ícono rojo, "No pudimos procesar tu pago", "Pagar con otra tarjeta" (limpia el formulario y lo muestra de nuevo) y "Volver al sitio".
  - **pending:** ícono amarillo, "Tu pago está en proceso" y "Volver al sitio".
  - **404 en datos:** "Preferencia inexistente" y un link a `/`.
  - **`pagada: true` o 409:** "Este pago ya fue realizado" y "Volver al sitio".
- **Logo:** archivo oficial de los recursos de marca de Mercado Pago, guardado como `logo.svg` (o `.png`, ajustando el HTML). Si no se consigue un archivo oficial, poner el texto "Mercado Pago" en blanco y negrita. **No dibujar una imitación del logo.**

- [ ] **Paso 1: implementar la página.**
- [ ] **Paso 2: comprobar a mano en el navegador** con `uvicorn app.main:app --reload`, sin `MP_ACCESS_TOKEN` en el `.env`:
  1. **Aprobado:** compra con tarjeta → "Pagar con Mercado Pago" → Mastercard 5031 7557 3453 0604, `APRO`, un vencimiento futuro, código 123, DNI 12345678 → "¡Listo!" → "Volver al sitio" → "¡Pago aprobado!" y el mail en el log.
  2. **Rechazado y reintento:** igual, con `OTHE` → "No pudimos procesar tu pago" → "Pagar con otra tarjeta" con `APRO` → aprobado.
  3. **Validaciones:** número 1234 5678 9012 3456 → "Revisá el número de tarjeta"; vencimiento del mes pasado → error.
  4. **Doble pago:** volver atrás en el navegador sobre una preferencia ya pagada → "Este pago ya fue realizado".
  5. **Datos que viajan:** en las herramientas de desarrollo (pestaña Red), el `POST .../pagos` lleva solo `titular`, `marca` y `ultimos_digitos`.
- [ ] **Paso 3: correr la batería completa** (sigue pasando) **y commitear** `Front: pagina de checkout del Mercado Pago simulado`.

---

### Tarea 6: verificación y documentación

**Archivos:**
- Modificar: `DECISIONES_DE_DISENO.md`, `CICLO_TDD.md`, `BACKLOG.md`, `README.md` y `CONFIGURACION_CREDENCIALES.md`

- [ ] **Paso 1: mutaciones.** Aplicar cada una sobre una copia, igual que en `CICLO_TDD.md`, sección 7.3, y comprobar que alguna prueba falla:
  - `APRO` da `rejected`.
  - El titular por defecto da `approved`.
  - El monto ignora `quantity`.
  - La URL de vuelta usa siempre `success`.
  - Se quita el control del token (401).
  - Un pago inexistente responde 200.
  - Se quita `extra="forbid"`.
  - Se quita el control de "ya pagada".
  - `init_point` sin `URL_PUBLICA`.
  - Se quita la normalización del titular.
  - `crear_pasarela_pago` sin credenciales no usa el simulador.

  Si alguna sobrevive, reforzar la prueba con un commit `Red`/`Green` o `Refactor` propio y registrarlo.
- [ ] **Paso 2: correr `pytest --cov=app`.** Anotar la cantidad de pruebas y la cobertura.
- [ ] **Paso 3: actualizar la documentación.**
  - **`DECISIONES_DE_DISENO.md`:** decisión 17, Mercado Pago simulado. Resumir el diseño y enlazar `docs/diseno-mercado-pago-simulado.md`. Ajustar la decisión 14: la pasarela simulada vieja ya no existe.
  - **`CICLO_TDD.md`:** sección 8, con la tabla de commits de los ciclos 19 a 22, los tipos de Red, las mutaciones y la prueba manual del paso 2 de la Tarea 5.
  - **`BACKLOG.md`:**
    - CP-35: pago rechazado en el checkout simulado, compra pendiente y reintento.
    - CP-36: preferencia ya pagada no acepta otro pago.
    - CP-37: el número de tarjeta no viaja al servidor.
    - Pruebas complementarias: titular → resultado, API simulada (401 y 404), página servida.
  - **`README.md`:** sección "Demo sin cuenta de Mercado Pago", con los pasos y las tarjetas y titulares de ejemplo.
  - **`CONFIGURACION_CREDENCIALES.md`:** al principio, que sin `MP_ACCESS_TOKEN` se usa el simulado y que para esta entrega el grupo usa ese modo.
- [ ] **Paso 4: commit** `Docs: Mercado Pago simulado, ciclos 19 a 22`.
