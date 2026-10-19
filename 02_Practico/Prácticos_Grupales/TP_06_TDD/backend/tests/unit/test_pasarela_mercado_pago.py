import json

import httpx
import pytest

from app.adaptadores.pasarela_pago import (
    URL_PREFERENCIAS_MERCADO_PAGO,
    PasarelaMercadoPago,
)
from app.dominio.errores import PagoNoDisponibleError
from app.dominio.modelos import Compra, MedioPago, TipoPase
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
