import json

import httpx
import pytest

from app.adaptadores.pasarela_pago import (
    URL_PAGOS_MERCADO_PAGO,
    URL_PREFERENCIAS_MERCADO_PAGO,
    PasarelaMercadoPago,
)
from app.dominio.errores import PagoNoDisponibleError
from app.dominio.modelos import (
    Compra,
    MedioPago,
    PagoInformado,
    TipoPase,
)
from tests.fechas import FECHA_VISITA

URL_RETORNO = "http://127.0.0.1:8000/"


def compra_con_tarjeta(**cambios):
    datos = {
        "email_usuario": "visitante@ecoharmony.com",
        "fecha_visita": FECHA_VISITA,
        "cantidad": 2,
        "edades": [40, 8],
        "tipo_pase": TipoPase.REGULAR,
        "medio_pago": MedioPago.TARJETA,
        "total": 15000,
        "id": 7,
    }
    datos.update(cambios)
    return Compra(**datos)


class MercadoPagoFalso:
    """Responde como la API de Mercado Pago y guarda lo que recibió."""

    def __init__(self, status_code=201):
        self.status_code = status_code
        self.solicitudes = []

    def __call__(self, solicitud):
        self.solicitudes.append(solicitud)
        return httpx.Response(
            self.status_code,
            json={
                "id": "pref-123",
                "init_point": "https://www.mercadopago.com.ar/checkout/v1/"
                "redirect?pref_id=pref-123",
                "sandbox_init_point": "https://sandbox.mercadopago.com.ar/"
                "checkout/v1/redirect?pref_id=pref-123",
            },
        )


def pasarela(api, access_token="TEST-123"):
    cliente = httpx.Client(transport=httpx.MockTransport(api))
    return PasarelaMercadoPago(access_token, URL_RETORNO, cliente)


def test_crea_la_preferencia_con_el_total_de_la_compra():
    api = MercadoPagoFalso()

    pasarela(api).crear_pago(compra_con_tarjeta())

    (solicitud,) = api.solicitudes
    assert solicitud.method == "POST"
    assert str(solicitud.url) == URL_PREFERENCIAS_MERCADO_PAGO
    assert solicitud.headers["Authorization"] == "Bearer TEST-123"
    preferencia = json.loads(solicitud.content)
    (item,) = preferencia["items"]
    assert item["quantity"] == 1
    assert item["unit_price"] == 15000
    assert item["currency_id"] == "ARS"
    assert preferencia["external_reference"] == "7"


def test_mercado_pago_vuelve_al_sitio_al_terminar_el_pago():
    api = MercadoPagoFalso()

    pasarela(api).crear_pago(compra_con_tarjeta())

    preferencia = json.loads(api.solicitudes[0].content)
    assert preferencia["back_urls"] == {
        "success": URL_RETORNO,
        "failure": URL_RETORNO,
        "pending": URL_RETORNO,
    }


def test_con_credenciales_de_prueba_redirige_al_checkout_de_prueba():
    url = pasarela(MercadoPagoFalso()).crear_pago(compra_con_tarjeta())

    assert url.startswith("https://sandbox.mercadopago.com.ar/")


def test_con_credenciales_de_produccion_redirige_al_checkout_real():
    url = pasarela(MercadoPagoFalso(), "APP_USR-123").crear_pago(
        compra_con_tarjeta()
    )

    assert url.startswith("https://www.mercadopago.com.ar/")


def test_si_mercado_pago_rechaza_la_preferencia_se_informa_el_error():
    with pytest.raises(PagoNoDisponibleError):
        pasarela(MercadoPagoFalso(status_code=401)).crear_pago(
            compra_con_tarjeta()
        )


def test_si_mercado_pago_no_responde_se_informa_el_error():
    def sin_conexion(solicitud):
        raise httpx.ConnectError("sin conexión", request=solicitud)

    with pytest.raises(PagoNoDisponibleError):
        pasarela(sin_conexion).crear_pago(compra_con_tarjeta())


# Vuelta automática al sitio: Mercado Pago solo la acepta con una URL
# pública (https), no con la dirección local de desarrollo.


def test_con_url_publica_vuelve_sola_al_sitio_al_aprobarse_el_pago():
    api = MercadoPagoFalso()
    cliente = httpx.Client(transport=httpx.MockTransport(api))
    pasarela_publica = PasarelaMercadoPago(
        "TEST-123", "https://ecoharmony.example/", cliente
    )

    pasarela_publica.crear_pago(compra_con_tarjeta())

    preferencia = json.loads(api.solicitudes[0].content)
    assert preferencia["auto_return"] == "approved"


def test_con_url_local_no_se_pide_la_vuelta_automatica():
    api = MercadoPagoFalso()

    pasarela(api).crear_pago(compra_con_tarjeta())

    preferencia = json.loads(api.solicitudes[0].content)
    assert "auto_return" not in preferencia


# Consulta del pago al volver del checkout (GET /v1/payments/{id}).


class ApiDePagosFalsa:
    """Responde como la consulta de pagos de Mercado Pago."""

    def __init__(self, status_code=200, **cambios):
        self.status_code = status_code
        self.pago = {
            "id": 123,
            "status": "approved",
            "external_reference": "7",
            "transaction_amount": 15000.0,
        } | cambios
        self.solicitudes = []

    def __call__(self, solicitud):
        self.solicitudes.append(solicitud)
        return httpx.Response(self.status_code, json=self.pago)


def test_consulta_el_pago_aprobado_a_mercado_pago():
    api = ApiDePagosFalsa()

    pago = pasarela(api).consultar_pago("123")

    (solicitud,) = api.solicitudes
    assert solicitud.method == "GET"
    assert str(solicitud.url) == f"{URL_PAGOS_MERCADO_PAGO}/123"
    assert solicitud.headers["Authorization"] == "Bearer TEST-123"
    assert pago == PagoInformado("123", True, 7, 15000)


@pytest.mark.parametrize("estado", ["rejected", "pending", "in_process"])
def test_un_pago_no_aprobado_se_informa_sin_aprobar(estado):
    pago = pasarela(ApiDePagosFalsa(status=estado)).consultar_pago("123")

    assert not pago.aprobado


def test_un_pago_sin_referencia_no_corresponde_a_ninguna_compra():
    api = ApiDePagosFalsa(external_reference=None)

    pago = pasarela(api).consultar_pago("123")

    assert pago.id_compra is None


def test_si_no_se_puede_consultar_el_pago_se_informa_el_error():
    with pytest.raises(PagoNoDisponibleError):
        pasarela(ApiDePagosFalsa(status_code=404)).consultar_pago("123")


def test_un_id_de_pago_que_no_es_numerico_no_se_consulta():
    # Evita armar la URL de la API con texto arbitrario recibido del front.
    api = ApiDePagosFalsa()

    pago = pasarela(api).consultar_pago("../usuarios")

    assert api.solicitudes == []
    assert not pago.aprobado
    assert pago.id_compra is None
