import pytest

from app.dependencias import obtener_mercado_pago_simulado
from app.main import app
from app.mercado_pago_simulado.nucleo import (
    TOKEN_SIMULADO,
    MercadoPagoSimulado,
)

DATOS_PREFERENCIA = {
    "items": [
        {
            "title": "EcoHarmony Park",
            "quantity": 1,
            "unit_price": 15000,
            "currency_id": "ARS",
        }
    ],
    "external_reference": "7",
    "back_urls": {
        "success": "http://testserver/",
        "failure": "http://testserver/",
        "pending": "http://testserver/",
    },
}
PAGO_APROBADO = {
    "titular": "APRO",
    "marca": "master",
    "ultimos_digitos": "0604",
}


@pytest.fixture
def mercado_pago_simulado():
    return MercadoPagoSimulado("http://testserver/")


@pytest.fixture
def checkout(client, mercado_pago_simulado):
    """Cliente cuyo checkout simulado usa el simulador de la prueba."""
    app.dependency_overrides[obtener_mercado_pago_simulado] = lambda: (
        mercado_pago_simulado
    )
    return client


def crear_preferencia(simulador, **cambios):
    return simulador.crear_preferencia({**DATOS_PREFERENCIA, **cambios})


def pagar(checkout, id_preferencia, **cambios):
    return checkout.post(
        f"/mercadopago-simulado/checkout/{id_preferencia}/pagos",
        json={**PAGO_APROBADO, **cambios},
    )


# Página y datos del checkout


def test_la_pagina_de_checkout_se_sirve_con_el_aviso_de_simulacion(checkout):
    respuesta = checkout.get("/mercadopago-simulado/checkout?pref_id=x")

    assert respuesta.status_code == 200
    assert respuesta.headers["content-type"].startswith("text/html")
    assert "Simulación · no se cobra dinero" in respuesta.text
    assert 'id="form-tarjeta"' in respuesta.text


def test_los_datos_del_checkout_informan_descripcion_y_total(
    checkout, mercado_pago_simulado
):
    pref = crear_preferencia(mercado_pago_simulado)

    respuesta = checkout.get(
        f"/mercadopago-simulado/checkout/{pref['id']}/datos"
    )

    assert respuesta.json() == {
        "descripcion": "EcoHarmony Park",
        "total": 15000,
        "pagada": False,
    }


def test_datos_de_una_preferencia_inexistente_responde_404(checkout):
    # Por ejemplo, si el servidor se reinició entre la compra y el pago.
    respuesta = checkout.get("/mercadopago-simulado/checkout/no-existe/datos")

    assert respuesta.status_code == 404
    assert respuesta.json()["detail"] == "Preferencia inexistente"


# Pago desde el formulario


def test_pagar_desde_el_checkout_devuelve_el_pago_y_la_url_de_vuelta(
    checkout, mercado_pago_simulado
):
    pref = crear_preferencia(mercado_pago_simulado)

    respuesta = pagar(checkout, pref["id"])

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["pago"]["status"] == "approved"
    assert cuerpo["url_de_vuelta"] == mercado_pago_simulado.url_de_vuelta(
        cuerpo["pago"]["id"]
    )
    assert cuerpo["volver_automaticamente"] is False


@pytest.mark.parametrize(
    "titular, vuelve_solo", [("APRO", True), ("OTHE", False)]
)
def test_con_auto_return_solo_un_pago_aprobado_vuelve_solo(
    checkout, mercado_pago_simulado, titular, vuelve_solo
):
    pref = crear_preferencia(mercado_pago_simulado, auto_return="approved")

    respuesta = pagar(checkout, pref["id"], titular=titular)

    assert respuesta.json()["volver_automaticamente"] is vuelve_solo


def test_pagar_una_preferencia_inexistente_responde_404(checkout):
    respuesta = pagar(checkout, "no-existe")

    assert respuesta.status_code == 404
    assert respuesta.json()["detail"] == "Preferencia inexistente"


def test_pagar_dos_veces_una_preferencia_aprobada_responde_409(
    checkout, mercado_pago_simulado
):
    pref = crear_preferencia(mercado_pago_simulado)
    pagar(checkout, pref["id"])

    respuesta = pagar(checkout, pref["id"])

    assert respuesta.status_code == 409
    assert respuesta.json()["detail"] == "Este pago ya fue realizado"
    datos = checkout.get(f"/mercadopago-simulado/checkout/{pref['id']}/datos")
    assert datos.json()["pagada"] is True


def test_el_numero_de_tarjeta_no_se_acepta_en_el_pago(
    checkout, mercado_pago_simulado
):
    pref = crear_preferencia(mercado_pago_simulado)

    respuesta = pagar(checkout, pref["id"], numero="5031755734530604")

    assert respuesta.status_code == 422
    assert mercado_pago_simulado.pagos_de_preferencia(pref["id"]) == []


@pytest.mark.parametrize(
    "cambios",
    [{"marca": "naranja"}, {"ultimos_digitos": "06"}, {"titular": ""}],
    ids=["marca", "ultimos-digitos", "titular"],
)
def test_datos_de_pago_invalidos_responden_422(
    checkout, mercado_pago_simulado, cambios
):
    pref = crear_preferencia(mercado_pago_simulado)

    respuesta = pagar(checkout, pref["id"], **cambios)

    assert respuesta.status_code == 422
    assert mercado_pago_simulado.pagos_de_preferencia(pref["id"]) == []


# La API simulada también se expone por HTTP (para /docs y curl).


def test_la_api_simulada_por_http_crea_y_consulta(
    checkout, mercado_pago_simulado
):
    cabeceras = {"Authorization": f"Bearer {TOKEN_SIMULADO}"}

    creada = checkout.post(
        "/mercadopago-simulado/api/checkout/preferences",
        headers=cabeceras,
        json=DATOS_PREFERENCIA,
    )
    pago = mercado_pago_simulado.pagar(
        creada.json()["id"], "APRO", "visa", "3704"
    )
    consultado = checkout.get(
        f"/mercadopago-simulado/api/v1/payments/{pago['id']}",
        headers=cabeceras,
    )

    assert creada.status_code == 201
    assert consultado.status_code == 200
    assert consultado.json()["status"] == "approved"


def test_la_api_simulada_por_http_sin_token_responde_401(checkout):
    respuesta = checkout.get("/mercadopago-simulado/api/v1/payments/1")

    assert respuesta.status_code == 401
