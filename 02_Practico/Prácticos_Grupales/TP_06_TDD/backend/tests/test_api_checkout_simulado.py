import pytest

from app.mercado_pago_simulado.nucleo import TOKEN_SIMULADO

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


def crear_preferencia(simulador, **cambios):
    return simulador.crear_preferencia({**DATOS_PREFERENCIA, **cambios})


def pagar(client, id_preferencia, **cambios):
    return client.post(
        f"/mercadopago-simulado/checkout/{id_preferencia}/pagos",
        json={**PAGO_APROBADO, **cambios},
    )


# Página y datos del checkout


def test_la_pagina_de_checkout_se_sirve_con_el_aviso_de_simulacion(client):
    respuesta = client.get("/mercadopago-simulado/checkout?pref_id=x")

    assert respuesta.status_code == 200
    assert respuesta.headers["content-type"].startswith("text/html")
    assert "Simulación · no se cobra dinero" in respuesta.text
    assert 'id="form-tarjeta"' in respuesta.text


def test_los_datos_del_checkout_informan_descripcion_y_total(
    client, mercado_pago_simulado
):
    pref = crear_preferencia(mercado_pago_simulado)

    respuesta = client.get(
        f"/mercadopago-simulado/checkout/{pref['id']}/datos"
    )

    assert respuesta.json() == {
        "descripcion": "EcoHarmony Park",
        "total": 15000,
        "pagada": False,
    }


def test_datos_de_una_preferencia_inexistente_responde_404(client):
    # Por ejemplo, si el servidor se reinició entre la compra y el pago.
    respuesta = client.get("/mercadopago-simulado/checkout/no-existe/datos")

    assert respuesta.status_code == 404
    assert respuesta.json()["detail"] == "Preferencia inexistente"


# Pago desde el formulario


def test_pagar_desde_el_checkout_devuelve_el_pago_y_la_url_de_vuelta(
    client, mercado_pago_simulado
):
    pref = crear_preferencia(mercado_pago_simulado)

    respuesta = pagar(client, pref["id"])

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
    client, mercado_pago_simulado, titular, vuelve_solo
):
    pref = crear_preferencia(mercado_pago_simulado, auto_return="approved")

    respuesta = pagar(client, pref["id"], titular=titular)

    assert respuesta.json()["volver_automaticamente"] is vuelve_solo


def test_pagar_una_preferencia_inexistente_responde_404(client):
    respuesta = pagar(client, "no-existe")

    assert respuesta.status_code == 404
    assert respuesta.json()["detail"] == "Preferencia inexistente"


def test_pagar_dos_veces_una_preferencia_aprobada_responde_409(
    client, mercado_pago_simulado
):
    pref = crear_preferencia(mercado_pago_simulado)
    pagar(client, pref["id"])

    respuesta = pagar(client, pref["id"])

    assert respuesta.status_code == 409
    assert respuesta.json()["detail"] == "Este pago ya fue realizado"
    datos = client.get(f"/mercadopago-simulado/checkout/{pref['id']}/datos")
    assert datos.json()["pagada"] is True


def test_el_numero_de_tarjeta_no_se_acepta_en_el_pago(
    client, mercado_pago_simulado
):
    pref = crear_preferencia(mercado_pago_simulado)

    respuesta = pagar(client, pref["id"], numero="5031755734530604")

    assert respuesta.status_code == 422
    assert mercado_pago_simulado.pagos_de_preferencia(pref["id"]) == []


@pytest.mark.parametrize(
    "cambios",
    [{"marca": "naranja"}, {"ultimos_digitos": "06"}, {"titular": ""}],
    ids=["marca", "ultimos-digitos", "titular"],
)
def test_datos_de_pago_invalidos_responden_422(
    client, mercado_pago_simulado, cambios
):
    pref = crear_preferencia(mercado_pago_simulado)

    respuesta = pagar(client, pref["id"], **cambios)

    assert respuesta.status_code == 422
    assert mercado_pago_simulado.pagos_de_preferencia(pref["id"]) == []


# La API simulada también se expone por HTTP (para /docs y curl).


def test_la_api_simulada_por_http_crea_y_consulta(
    client, mercado_pago_simulado
):
    cabeceras = {"Authorization": f"Bearer {TOKEN_SIMULADO}"}

    creada = client.post(
        "/mercadopago-simulado/api/checkout/preferences",
        headers=cabeceras,
        json=DATOS_PREFERENCIA,
    )
    pago = mercado_pago_simulado.pagar(
        creada.json()["id"], "APRO", "visa", "3704"
    )
    consultado = client.get(
        f"/mercadopago-simulado/api/v1/payments/{pago['id']}",
        headers=cabeceras,
    )

    assert creada.status_code == 201
    assert consultado.status_code == 200
    assert consultado.json()["status"] == "approved"


def test_la_api_simulada_por_http_sin_token_responde_401(client):
    respuesta = client.get("/mercadopago-simulado/api/v1/payments/1")

    assert respuesta.status_code == 401
