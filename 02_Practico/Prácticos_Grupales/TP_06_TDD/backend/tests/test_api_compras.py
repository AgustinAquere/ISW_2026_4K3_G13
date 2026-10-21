from datetime import timedelta
from urllib.parse import parse_qs, urlsplit

import pytest

from app.dominio.errores import PagoNoDisponibleError
from tests.fechas import FECHA_VISITA, HOY, LUNES_PROXIMO, UN_DIA, dd_mm_aaaa


def solicitud_valida(**cambios):
    """Arma un cuerpo de compra válido.

    Cada prueba cambia solo el dato que evalúa.
    """
    solicitud = {
        "fecha_visita": FECHA_VISITA.isoformat(),
        "cantidad": 2,
        "edades": [25, 30],
        "tipo_pase": "REGULAR",
        "medio_pago": "EFECTIVO",
    }
    solicitud.update(cambios)
    return solicitud


def id_de_pago(url_de_vuelta):
    """Lee el pago de la URL con la que Mercado Pago vuelve al sitio."""
    return parse_qs(urlsplit(url_de_vuelta).query)["payment_id"][0]


def pagar_en_checkout(client, url_pago, titular):
    """Paga en el checkout simulado, como el profesor en la demo.

    Devuelve la URL con la que Mercado Pago vuelve al sitio.
    """
    (id_preferencia,) = parse_qs(urlsplit(url_pago).query)["pref_id"]
    respuesta = client.post(
        f"/mercadopago-simulado/checkout/{id_preferencia}/pagos",
        json={
            "titular": titular,
            "marca": "master",
            "ultimos_digitos": "0604",
        },
    )
    return respuesta.json()["url_de_vuelta"]


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
    assert cuerpo["url_pago"].startswith(
        "http://testserver/mercadopago-simulado/checkout?pref_id="
    )
    assert cuerpo["cantidad"] == 3
    assert cuerpo["fecha_visita"] == FECHA_VISITA.isoformat()
    assert cuerpo["total"] == 50000  # 2 VIP completos + 1 VIP al 50 %
    assert cuerpo["estado"] == "PENDIENTE_DE_PAGO"
    # El mail de confirmación se envía cuando Mercado Pago aprueba el
    # pago.
    assert notificador.enviados == []

    # Pago con tarjeta en el checkout y vuelta al sitio, como hace el
    # front.
    vuelta = pagar_en_checkout(client, cuerpo["url_pago"], "APRO")
    confirmacion = client.post(
        f"/compras/{cuerpo['id']}/pago",
        json={"id_pago": id_de_pago(vuelta)},
        headers=cabecera_usuario,
    )

    assert confirmacion.status_code == 200
    assert confirmacion.json()["estado"] == "CONFIRMADA"
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
        json=solicitud_valida(fecha_visita=LUNES_PROXIMO.isoformat()),
        headers=cabecera_usuario,
    )

    assert respuesta.status_code == 400
    assert "cerrado" in respuesta.json()["detail"]


@pytest.mark.parametrize(
    "cambios, mensaje",
    [
        ({"fecha_visita": (HOY - UN_DIA).isoformat()}, "pasada"),
        ({"fecha_visita": (HOY + timedelta(days=32)).isoformat()}, "31 días"),
        ({"cantidad": 0, "edades": []}, "cantidad"),
        ({"cantidad": 3, "edades": [25, 30]}, "edad"),
        ({"edades": [25, -1]}, "edad"),
        ({"edades": [25, 549]}, "100 años"),
    ],
    ids=["CP-12", "CP-16", "CP-08", "CP-27", "CP-18", "CP-39"],
)
def test_api_rechaza_la_compra_con_un_mensaje_claro(
    client, cabecera_usuario, cambios, mensaje
):
    respuesta = client.post(
        "/compras",
        json=solicitud_valida(**cambios),
        headers=cabecera_usuario,
    )

    assert respuesta.status_code == 400
    assert mensaje in respuesta.json()["detail"]


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
    assert respuesta.json()["estado"] == "CONFIRMADA"


def test_cp26_api_informa_cantidad_y_fecha_al_finalizar(
    client, cabecera_usuario
):
    respuesta = client.post(
        "/compras", json=solicitud_valida(), headers=cabecera_usuario
    )

    assert (
        respuesta.json()["mensaje"]
        == f"Compraste 2 entradas para el {dd_mm_aaaa(FECHA_VISITA)}"
    )


def test_api_informa_si_mercado_pago_no_esta_disponible(
    client, cabecera_usuario, pasarela_pago, monkeypatch
):
    def mercado_pago_caido(compra):
        raise PagoNoDisponibleError()

    monkeypatch.setattr(pasarela_pago, "crear_pago", mercado_pago_caido)

    respuesta = client.post(
        "/compras",
        json=solicitud_valida(medio_pago="TARJETA"),
        headers=cabecera_usuario,
    )

    assert respuesta.status_code == 502
    assert "Mercado Pago" in respuesta.json()["detail"]


# 7. Confirmación del pago al volver de Mercado Pago


def comprar_con_tarjeta(client, cabecera_usuario):
    respuesta = client.post(
        "/compras",
        json=solicitud_valida(medio_pago="TARJETA"),
        headers=cabecera_usuario,
    )
    return respuesta.json()


def test_confirmar_el_pago_sin_iniciar_sesion_es_rechazado(
    client, cabecera_usuario
):
    compra = comprar_con_tarjeta(client, cabecera_usuario)

    vuelta = pagar_en_checkout(client, compra["url_pago"], "APRO")

    respuesta = client.post(
        f"/compras/{compra['id']}/pago",
        json={"id_pago": id_de_pago(vuelta)},
    )

    assert respuesta.status_code == 401
    assert respuesta.json()["detail"] == "Debe iniciar sesión"


def test_confirmar_el_pago_de_una_compra_inexistente_responde_404(
    client, cabecera_usuario
):
    respuesta = client.post(
        "/compras/99/pago", json={"id_pago": "1"}, headers=cabecera_usuario
    )

    assert respuesta.status_code == 404


def test_confirmar_un_pago_que_no_corresponde_a_la_compra_responde_400(
    client, cabecera_usuario, notificador
):
    compra = comprar_con_tarjeta(client, cabecera_usuario)
    otra_compra = comprar_con_tarjeta(client, cabecera_usuario)
    vuelta = pagar_en_checkout(client, otra_compra["url_pago"], "APRO")

    # El pago es de la otra compra.
    respuesta = client.post(
        f"/compras/{compra['id']}/pago",
        json={"id_pago": id_de_pago(vuelta)},
        headers=cabecera_usuario,
    )

    assert respuesta.status_code == 400
    assert "no corresponde" in respuesta.json()["detail"]
    assert notificador.enviados == []


def test_api_informa_si_no_se_puede_consultar_el_pago(
    client, cabecera_usuario, pasarela_pago, monkeypatch
):
    compra = comprar_con_tarjeta(client, cabecera_usuario)
    vuelta = pagar_en_checkout(client, compra["url_pago"], "APRO")

    def mercado_pago_caido(id_pago):
        raise PagoNoDisponibleError()

    monkeypatch.setattr(pasarela_pago, "consultar_pago", mercado_pago_caido)

    respuesta = client.post(
        f"/compras/{compra['id']}/pago",
        json={"id_pago": id_de_pago(vuelta)},
        headers=cabecera_usuario,
    )

    assert respuesta.status_code == 502
    assert "Mercado Pago" in respuesta.json()["detail"]


def test_confirmar_con_un_pago_inexistente_responde_502(
    client, cabecera_usuario
):
    # Mercado Pago no conoce ese pago (por ejemplo, se reinició el
    # servidor).
    compra = comprar_con_tarjeta(client, cabecera_usuario)

    respuesta = client.post(
        f"/compras/{compra['id']}/pago",
        json={"id_pago": "999"},
        headers=cabecera_usuario,
    )

    assert respuesta.status_code == 502
    assert "Mercado Pago" in respuesta.json()["detail"]


def test_cp35_pago_rechazado_deja_la_compra_pendiente_y_se_puede_reintentar(
    client, cabecera_usuario, notificador
):
    compra = comprar_con_tarjeta(client, cabecera_usuario)

    rechazado = pagar_en_checkout(client, compra["url_pago"], "OTHE")
    respuesta = client.post(
        f"/compras/{compra['id']}/pago",
        json={"id_pago": id_de_pago(rechazado)},
        headers=cabecera_usuario,
    )

    assert respuesta.json()["estado"] == "PENDIENTE_DE_PAGO"
    assert notificador.enviados == []

    # "Pagar con otra tarjeta" en el checkout: misma preferencia, otro
    # pago.
    aprobado = pagar_en_checkout(client, compra["url_pago"], "APRO")
    respuesta = client.post(
        f"/compras/{compra['id']}/pago",
        json={"id_pago": id_de_pago(aprobado)},
        headers=cabecera_usuario,
    )

    assert respuesta.json()["estado"] == "CONFIRMADA"
    assert len(notificador.enviados) == 1


# 8. Verificación del pago hecho en otra pestaña: el sitio no recibe el
# id del pago y le pregunta al backend si la compra ya se pagó.


def verificar(client, compra, cabeceras):
    return client.post(
        f"/compras/{compra['id']}/verificacion-de-pago", headers=cabeceras
    )


def test_cp36_api_verifica_el_pago_hecho_en_otra_pestana(
    client, cabecera_usuario, notificador
):
    compra = comprar_con_tarjeta(client, cabecera_usuario)
    pagar_en_checkout(client, compra["url_pago"], "APRO")

    respuesta = verificar(client, compra, cabecera_usuario)

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["estado"] == "CONFIRMADA"
    assert cuerpo["pago"] == "aprobado"
    assert cuerpo["mensaje"] == compra["mensaje"]
    assert len(notificador.enviados) == 1


@pytest.mark.parametrize(
    "titular, pago", [("OTHE", "rechazado"), ("CONT", "pendiente")]
)
def test_api_verificacion_informa_el_pago_no_aprobado(
    client, cabecera_usuario, notificador, titular, pago
):
    compra = comprar_con_tarjeta(client, cabecera_usuario)
    pagar_en_checkout(client, compra["url_pago"], titular)

    cuerpo = verificar(client, compra, cabecera_usuario).json()

    assert cuerpo["estado"] == "PENDIENTE_DE_PAGO"
    assert cuerpo["pago"] == pago
    assert notificador.enviados == []


def test_api_verificacion_sin_pago_todavia(client, cabecera_usuario):
    compra = comprar_con_tarjeta(client, cabecera_usuario)

    cuerpo = verificar(client, compra, cabecera_usuario).json()

    assert cuerpo["estado"] == "PENDIENTE_DE_PAGO"
    assert cuerpo["pago"] == "sin_pago"


def test_api_verificacion_de_una_compra_confirmada_informa_aprobado(
    client, cabecera_usuario, notificador
):
    compra = comprar_con_tarjeta(client, cabecera_usuario)
    pagar_en_checkout(client, compra["url_pago"], "APRO")
    verificar(client, compra, cabecera_usuario)

    cuerpo = verificar(client, compra, cabecera_usuario).json()

    assert cuerpo["pago"] == "aprobado"
    assert len(notificador.enviados) == 1


def test_api_verificacion_sin_sesion_responde_401(client, cabecera_usuario):
    compra = comprar_con_tarjeta(client, cabecera_usuario)

    respuesta = verificar(client, compra, {})

    assert respuesta.status_code == 401


def test_api_verificacion_de_una_compra_inexistente_responde_404(
    client, cabecera_usuario
):
    respuesta = verificar(client, {"id": 99}, cabecera_usuario)

    assert respuesta.status_code == 404


def test_api_verificacion_con_mercado_pago_caido_responde_502(
    client, cabecera_usuario, pasarela_pago, monkeypatch
):
    compra = comprar_con_tarjeta(client, cabecera_usuario)

    def mercado_pago_caido(id_compra):
        raise PagoNoDisponibleError()

    monkeypatch.setattr(pasarela_pago, "buscar_pago", mercado_pago_caido)

    respuesta = verificar(client, compra, cabecera_usuario)

    assert respuesta.status_code == 502
    assert "Mercado Pago" in respuesta.json()["detail"]


def test_cp37_un_pago_ajeno_con_el_mismo_numero_de_compra_no_la_confirma(
    client, cabecera_usuario, mercado_pago_simulado, notificador
):
    compra = comprar_con_tarjeta(client, cabecera_usuario)
    # Pago aprobado de otra compra con el mismo número y el mismo total
    # (de una base anterior o de otro integrante con las mismas
    # credenciales).
    ajena = mercado_pago_simulado.crear_preferencia(
        {
            "items": [
                {"title": "otra", "quantity": 1, "unit_price": compra["total"]}
            ],
            "external_reference": str(compra["id"]),
            "back_urls": dict.fromkeys(
                ("success", "failure", "pending"), "http://otro-sitio/"
            ),
        }
    )
    mercado_pago_simulado.pagar(ajena["id"], "APRO", "visa", "3704")

    cuerpo = verificar(client, compra, cabecera_usuario).json()

    assert cuerpo["estado"] == "PENDIENTE_DE_PAGO"
    assert cuerpo["pago"] == "sin_pago"
    assert notificador.enviados == []
