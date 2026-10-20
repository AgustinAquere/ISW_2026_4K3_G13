import httpx
import pytest

from app.adaptadores.pasarela_pago import PasarelaMercadoPago
from app.dominio.errores import PagoNoDisponibleError
from app.dominio.modelos import Compra, MedioPago, PagoInformado, TipoPase
from app.mercado_pago_simulado.api import (
    PREFIJO_API_SIMULADA,
    responder_api,
    transporte_en_proceso,
)
from app.mercado_pago_simulado.nucleo import (
    TOKEN_SIMULADO,
    MercadoPagoSimulado,
)
from tests.fechas import FECHA_VISITA

URL_PUBLICA = "http://127.0.0.1:8000/"
AUTORIZACION = f"Bearer {TOKEN_SIMULADO}"


@pytest.fixture
def simulador():
    return MercadoPagoSimulado(URL_PUBLICA)


def compra_con_tarjeta():
    return Compra(
        email_usuario="visitante@ecoharmony.com",
        fecha_visita=FECHA_VISITA,
        cantidad=2,
        edades=[40, 8],
        tipo_pase=TipoPase.REGULAR,
        medio_pago=MedioPago.TARJETA,
        total=15000,
        id=7,
    )


def pasarela_simulada(simulador):
    cliente = httpx.Client(transport=transporte_en_proceso(simulador))
    return PasarelaMercadoPago(
        TOKEN_SIMULADO,
        URL_PUBLICA,
        cliente,
        url_api=URL_PUBLICA.rstrip("/") + PREFIJO_API_SIMULADA,
    )


# Contrato de la API simulada: el mismo que la API de Mercado Pago.


def test_sin_token_la_api_responde_401(simulador):
    estado, cuerpo = responder_api(
        simulador, "GET", "/v1/payments/1", None, None
    )

    assert estado == 401
    assert cuerpo["status"] == 401


def test_con_otro_token_la_api_responde_401(simulador):
    estado, _ = responder_api(
        simulador,
        "POST",
        "/checkout/preferences",
        "Bearer TEST-123",
        {"items": []},
    )

    assert estado == 401


def test_la_api_crea_la_preferencia(simulador):
    datos = {
        "items": [{"title": "a", "quantity": 1, "unit_price": 100}],
        "external_reference": "7",
        "back_urls": {"success": "http://sitio/"},
    }

    estado, cuerpo = responder_api(
        simulador, "POST", "/checkout/preferences", AUTORIZACION, datos
    )

    assert estado == 201
    assert simulador.obtener_preferencia(cuerpo["id"]) == cuerpo


@pytest.mark.parametrize("id_pago", ["999", "abc"])
def test_un_pago_inexistente_responde_404(simulador, id_pago):
    estado, cuerpo = responder_api(
        simulador, "GET", f"/v1/payments/{id_pago}", AUTORIZACION, None
    )

    assert estado == 404
    assert cuerpo["error"] == "not_found"


def test_un_camino_desconocido_responde_404(simulador):
    estado, _ = responder_api(simulador, "GET", "/v1/otro", AUTORIZACION, None)

    assert estado == 404


# PasarelaMercadoPago es la misma clase en los dos modos: en el simulado
# le habla al simulador por un transporte dentro del mismo proceso.


def test_la_pasarela_crea_la_preferencia_en_el_simulador(simulador):
    url = pasarela_simulada(simulador).crear_pago(compra_con_tarjeta())

    (pref,) = simulador.preferencias_creadas()
    assert url == pref["init_point"]
    assert pref["external_reference"] == "7"
    assert simulador.total(pref["id"]) == 15000


@pytest.mark.parametrize(
    "titular, aprobado", [("APRO", True), ("OTHE", False)]
)
def test_la_pasarela_informa_el_pago_del_simulador(
    simulador, titular, aprobado
):
    pasarela = pasarela_simulada(simulador)
    pasarela.crear_pago(compra_con_tarjeta())
    (pref,) = simulador.preferencias_creadas()
    pago = simulador.pagar(pref["id"], titular, "master", "0604")

    informado = pasarela.consultar_pago(str(pago["id"]))

    assert informado == PagoInformado(
        str(pago["id"]), aprobado, "7", 15000, rechazado=not aprobado
    )


def test_un_pago_desconocido_por_el_simulador_es_pago_no_disponible(
    simulador,
):
    with pytest.raises(PagoNoDisponibleError):
        pasarela_simulada(simulador).consultar_pago("999")


def test_por_defecto_la_pasarela_usa_la_api_real():
    solicitudes = []

    def api_real(solicitud):
        solicitudes.append(solicitud)
        return httpx.Response(
            201, json={"init_point": "real", "sandbox_init_point": "prueba"}
        )

    cliente = httpx.Client(transport=httpx.MockTransport(api_real))
    PasarelaMercadoPago("TEST-1", URL_PUBLICA, cliente).crear_pago(
        compra_con_tarjeta()
    )

    assert str(solicitudes[0].url) == (
        "https://api.mercadopago.com/checkout/preferences"
    )


# Búsqueda de pagos por número de compra (GET /v1/payments/search).


def test_la_api_busca_los_pagos_por_referencia(simulador):
    datos = {
        "items": [{"title": "a", "quantity": 1, "unit_price": 100}],
        "external_reference": "7",
        "back_urls": {"success": "http://sitio/", "failure": "http://sitio/"},
    }
    pref = simulador.crear_preferencia(datos)
    rechazado = simulador.pagar(pref["id"], "OTHE", "visa", "3704")
    aprobado = simulador.pagar(pref["id"], "APRO", "visa", "3704")

    estado, cuerpo = responder_api(
        simulador,
        "GET",
        "/v1/payments/search",
        AUTORIZACION,
        None,
        {"external_reference": "7"},
    )

    assert estado == 200
    assert cuerpo["paging"]["total"] == 2
    # El más reciente primero, como con sort=date_created y
    # criteria=desc.
    assert [pago["id"] for pago in cuerpo["results"]] == [
        aprobado["id"],
        rechazado["id"],
    ]


def test_la_busqueda_de_otra_referencia_no_devuelve_pagos(simulador):
    estado, cuerpo = responder_api(
        simulador,
        "GET",
        "/v1/payments/search",
        AUTORIZACION,
        None,
        {"external_reference": "99"},
    )

    assert estado == 200
    assert cuerpo["results"] == []


def test_la_pasarela_busca_el_pago_en_el_simulador(simulador):
    pasarela = pasarela_simulada(simulador)
    pasarela.crear_pago(compra_con_tarjeta())
    (pref,) = simulador.preferencias_creadas()
    pago = simulador.pagar(pref["id"], "APRO", "master", "0604")

    informado = pasarela.buscar_pago(7)

    assert informado == PagoInformado(str(pago["id"]), True, "7", 15000)


# El transporte en proceso atiende solo la ruta de la API simulada, como
# un servidor real: si la pasarela le hablara a otra dirección, no
# respondería.


def test_el_transporte_solo_atiende_la_api_simulada(simulador):
    cliente = httpx.Client(transport=transporte_en_proceso(simulador))

    respuesta = cliente.get(
        "https://api.mercadopago.com/v1/payments/search",
        headers={"Authorization": AUTORIZACION},
    )

    assert respuesta.status_code == 404


def test_la_pasarela_usa_la_url_de_la_api_que_recibe(simulador):
    cliente = httpx.Client(transport=transporte_en_proceso(simulador))
    sin_url_simulada = PasarelaMercadoPago(
        TOKEN_SIMULADO, URL_PUBLICA, cliente
    )

    with pytest.raises(PagoNoDisponibleError):
        sin_url_simulada.crear_pago(compra_con_tarjeta())
