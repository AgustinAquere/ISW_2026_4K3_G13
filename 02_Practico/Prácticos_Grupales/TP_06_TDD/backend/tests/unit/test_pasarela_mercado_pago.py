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


def test_un_pago_rechazado_se_informa_como_rechazado():
    pago = pasarela(ApiDePagosFalsa(status="rejected")).consultar_pago("123")

    assert pago.rechazado
    assert not pago.aprobado


# Búsqueda de los pagos de una compra: cuando Mercado Pago se abre en otra
# pestaña, el sitio no recibe el id del pago y lo busca por el número de
# compra (external_reference).


class BusquedaDePagosFalsa:
    """Responde como GET /v1/payments/search de Mercado Pago."""

    def __init__(self, *pagos, status_code=200):
        self.pagos = list(pagos)
        self.status_code = status_code
        self.solicitudes = []

    def __call__(self, solicitud):
        self.solicitudes.append(solicitud)
        return httpx.Response(
            self.status_code,
            json={
                "paging": {"total": len(self.pagos)},
                "results": self.pagos,
            },
        )


def pago_de_mercado_pago(id_pago, estado, monto=15000.0, referencia="7"):
    return {
        "id": id_pago,
        "status": estado,
        "external_reference": referencia,
        "transaction_amount": monto,
    }


def test_busca_los_pagos_de_la_compra_por_su_numero():
    api = BusquedaDePagosFalsa(pago_de_mercado_pago(123, "approved"))

    pago = pasarela(api).buscar_pago(7)

    (solicitud,) = api.solicitudes
    assert solicitud.method == "GET"
    assert str(solicitud.url).startswith(f"{URL_PAGOS_MERCADO_PAGO}/search?")
    assert solicitud.url.params["external_reference"] == "7"
    assert solicitud.url.params["sort"] == "date_created"
    assert solicitud.url.params["criteria"] == "desc"
    assert solicitud.headers["Authorization"] == "Bearer TEST-123"
    assert pago == PagoInformado("123", True, 7, 15000)


def test_sin_pagos_la_busqueda_no_informa_ninguno():
    assert pasarela(BusquedaDePagosFalsa()).buscar_pago(7) is None


def test_si_hay_un_pago_aprobado_se_informa_ese_aunque_haya_otros():
    api = BusquedaDePagosFalsa(
        pago_de_mercado_pago(2, "rejected"),
        pago_de_mercado_pago(1, "approved"),
    )

    assert pasarela(api).buscar_pago(7).id_pago == "1"


def test_sin_pago_aprobado_se_informa_el_mas_reciente():
    api = BusquedaDePagosFalsa(
        pago_de_mercado_pago(2, "rejected"),
        pago_de_mercado_pago(1, "pending"),
    )

    pago = pasarela(api).buscar_pago(7)

    assert pago.id_pago == "2"
    assert pago.rechazado


def test_un_pago_pendiente_no_esta_aprobado_ni_rechazado():
    api = BusquedaDePagosFalsa(pago_de_mercado_pago(1, "in_process"))

    pago = pasarela(api).buscar_pago(7)

    assert not pago.aprobado
    assert not pago.rechazado


def test_si_no_se_puede_buscar_el_pago_se_informa_el_error():
    with pytest.raises(PagoNoDisponibleError):
        pasarela(BusquedaDePagosFalsa(status_code=500)).buscar_pago(7)


# Mercado Pago le quita las barras al título ("20/10/2026" se ve "20102026"):
# la fecha va escrita con palabras.
MESES = (
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
)


def test_el_titulo_del_pago_escribe_la_fecha_con_palabras():
    api = MercadoPagoFalso()

    pasarela(api).crear_pago(compra_con_tarjeta())

    (item,) = json.loads(api.solicitudes[0].content)["items"]
    fecha = (
        f"{FECHA_VISITA.day} de {MESES[FECHA_VISITA.month - 1]} "
        f"de {FECHA_VISITA.year}"
    )
    assert item["title"] == (
        f"EcoHarmony Park: 2 entradas REGULAR para el {fecha}"
    )
    assert "/" not in item["title"]
