from tests.fechas import HOY, LUNES_PROXIMO


def test_la_pagina_de_compra_se_sirve_en_la_raiz(client):
    respuesta = client.get("/")

    assert respuesta.status_code == 200
    assert respuesta.headers["content-type"].startswith("text/html")
    assert "EcoHarmony Park" in respuesta.text


def test_api_informa_las_fechas_disponibles(client):
    respuesta = client.get("/fechas-disponibles")

    assert respuesta.status_code == 200
    fechas = respuesta.json()["fechas"]
    assert fechas[0] == HOY.isoformat()
    assert LUNES_PROXIMO.isoformat() not in fechas


def test_api_cotiza_el_total_antes_de_elegir_la_forma_de_pago(client):
    # Adulto (precio completo) + niño de 8 (50 %) + bebé de 2 (gratis).
    respuesta = client.post(
        "/cotizacion", json={"edades": [40, 8, 2], "tipo_pase": "REGULAR"}
    )

    assert respuesta.status_code == 200
    assert respuesta.json() == {"total": 15000}


def test_api_no_cotiza_edades_negativas(client):
    respuesta = client.post(
        "/cotizacion", json={"edades": [40, -1], "tipo_pase": "REGULAR"}
    )

    assert respuesta.status_code == 422
