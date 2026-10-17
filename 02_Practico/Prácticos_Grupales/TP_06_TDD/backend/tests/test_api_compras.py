import pytest


def solicitud_valida(**cambios):
    """Arma un cuerpo de compra válido.

    Cada prueba cambia solo el dato que evalúa.
    """
    solicitud = {
        "fecha_visita": "2026-11-15",
        "cantidad": 2,
        "edades": [25, 30],
        "tipo_pase": "REGULAR",
        "medio_pago": "EFECTIVO",
    }
    solicitud.update(cambios)
    return solicitud


def solicitud_sin(campo):
    solicitud = solicitud_valida()
    del solicitud[campo]
    return solicitud


# 1. Compra y datos obligatorios


@pytest.mark.parametrize(
    "campo_faltante",
    ["medio_pago", "fecha_visita", "cantidad", "edades", "tipo_pase"],
    ids=["CP-02", "CP-03", "CP-04", "CP-05", "CP-06"],
)
def test_comprar_sin_dato_obligatorio_es_rechazado(
    client, cabecera_usuario, campo_faltante
):
    respuesta = client.post(
        "/compras",
        json=solicitud_sin(campo_faltante),
        headers=cabecera_usuario,
    )

    assert respuesta.status_code == 422


def test_cp07_comprar_sin_iniciar_sesion_es_rechazado(client):
    respuesta = client.post("/compras", json=solicitud_valida())

    assert respuesta.status_code == 401
    assert respuesta.json()["detail"] == "Debe iniciar sesión"


def test_cp07_comprar_con_usuario_no_registrado_es_rechazado(client):
    respuesta = client.post(
        "/compras",
        json=solicitud_valida(),
        headers={"X-Usuario-Email": "desconocido@mail.com"},
    )

    assert respuesta.status_code == 401
    assert respuesta.json()["detail"] == "Usuario no registrado"


def test_cp01_compra_con_tarjeta_mediante_mercado_pago_y_mail(
    client, cabecera_usuario, notificador
):
    respuesta = client.post(
        "/compras",
        json=solicitud_valida(
            cantidad=3,
            edades=[35, 33, 8],
            tipo_pase="VIP",
            medio_pago="TARJETA",
        ),
        headers=cabecera_usuario,
    )

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["url_pago"].startswith("https://www.mercadopago.com.ar/")
    assert cuerpo["cantidad"] == 3
    assert cuerpo["fecha_visita"] == "2026-11-15"
    assert cuerpo["total"] == 50000  # 2 VIP completos + 1 VIP al 50 %
    assert len(notificador.enviados) == 1


@pytest.mark.parametrize(
    "campo, valor",
    [("tipo_pase", "COMUN"), ("medio_pago", "CHEQUE")],
    ids=["tipo-pase-inexistente", "medio-pago-inexistente"],
)
def test_opcion_inexistente_es_rechazada(
    client, cabecera_usuario, campo, valor
):
    respuesta = client.post(
        "/compras",
        json=solicitud_valida(**{campo: valor}),
        headers=cabecera_usuario,
    )

    assert respuesta.status_code == 422


# 2 y 3. Reglas de negocio expuestas por la API


def test_cp10_api_rechaza_mas_de_10_entradas_con_mensaje(
    client, cabecera_usuario
):
    respuesta = client.post(
        "/compras",
        json=solicitud_valida(cantidad=11, edades=[30] * 11),
        headers=cabecera_usuario,
    )

    assert respuesta.status_code == 400
    assert "cantidad" in respuesta.json()["detail"]


def test_api_rechaza_fecha_con_parque_cerrado(client, cabecera_usuario):
    respuesta = client.post(
        "/compras",
        json=solicitud_valida(fecha_visita="2026-11-16"),  # lunes
        headers=cabecera_usuario,
    )

    assert respuesta.status_code == 400
    assert "cerrado" in respuesta.json()["detail"]


# 5 y 6. Pago y confirmación


def test_cp23_api_compra_en_boleteria_sin_url_de_pago(
    client, cabecera_usuario
):
    respuesta = client.post(
        "/compras",
        json=solicitud_valida(medio_pago="EFECTIVO"),
        headers=cabecera_usuario,
    )

    assert respuesta.status_code == 201
    assert respuesta.json()["url_pago"] is None


def test_cp26_api_informa_cantidad_y_fecha_al_finalizar(
    client, cabecera_usuario
):
    respuesta = client.post(
        "/compras", json=solicitud_valida(), headers=cabecera_usuario
    )

    assert (
        respuesta.json()["mensaje"]
        == "Compraste 2 entradas para el 15/11/2026"
    )
