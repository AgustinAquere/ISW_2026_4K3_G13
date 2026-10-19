from urllib.parse import parse_qs, urlsplit

import pytest

from app.mercado_pago_simulado.nucleo import (
    MercadoPagoSimulado,
    PreferenciaInexistenteError,
    PreferenciaYaPagadaError,
)

BACK_URLS = {
    "success": "http://sitio/ok",
    "failure": "http://sitio/mal",
    "pending": "http://sitio/pend",
}


@pytest.fixture
def simulador():
    # Sin barra final a propósito: la URL pública se normaliza.
    return MercadoPagoSimulado("http://127.0.0.1:8000")


def preferencia(simulador, **cambios):
    """Crea una preferencia válida; cada prueba cambia solo lo que evalúa."""
    datos = {
        "items": [
            {
                "title": "EcoHarmony Park",
                "quantity": 1,
                "unit_price": 15000,
                "currency_id": "ARS",
            }
        ],
        "external_reference": "7",
        "back_urls": BACK_URLS,
    }
    datos.update(cambios)
    return simulador.crear_preferencia(datos)


def test_la_preferencia_lleva_al_checkout_simulado(simulador):
    pref = preferencia(simulador)

    assert pref["init_point"] == (
        "http://127.0.0.1:8000/mercadopago-simulado/checkout"
        f"?pref_id={pref['id']}"
    )
    assert pref["sandbox_init_point"] == pref["init_point"]
    guardada = simulador.obtener_preferencia(pref["id"])
    assert guardada["external_reference"] == "7"


def test_una_preferencia_inexistente_no_se_encuentra(simulador):
    assert simulador.obtener_preferencia("no-existe") is None


def test_el_total_suma_precio_por_cantidad(simulador):
    pref = preferencia(
        simulador,
        items=[
            {
                "title": "a",
                "quantity": 2,
                "unit_price": 5000,
                "currency_id": "ARS",
            },
            {
                "title": "b",
                "quantity": 1,
                "unit_price": 3000,
                "currency_id": "ARS",
            },
        ],
    )

    assert simulador.total(pref["id"]) == 13000


@pytest.mark.parametrize(
    "titular, estado, detalle",
    [
        ("APRO", "approved", "accredited"),
        ("CONT", "pending", "pending_contingency"),
        ("OTHE", "rejected", "cc_rejected_other_reason"),
        ("FUND", "rejected", "cc_rejected_insufficient_amount"),
        ("SECU", "rejected", "cc_rejected_bad_filled_security_code"),
        ("JUAN PEREZ", "rejected", "cc_rejected_other_reason"),
    ],
)
def test_el_titular_define_el_resultado(simulador, titular, estado, detalle):
    pref = preferencia(simulador)

    pago = simulador.pagar(pref["id"], titular, "master", "0604")

    assert (pago["status"], pago["status_detail"]) == (estado, detalle)


def test_el_titular_se_compara_sin_mayusculas_ni_espacios(simulador):
    pref = preferencia(simulador)

    pago = simulador.pagar(pref["id"], "  apro ", "visa", "3704")

    assert pago["status"] == "approved"


def test_el_pago_queda_registrado_con_el_monto_y_la_referencia(simulador):
    pref = preferencia(simulador)

    pago = simulador.pagar(pref["id"], "APRO", "master", "0604")

    assert simulador.obtener_pago(pago["id"]) == pago
    assert pago["transaction_amount"] == 15000
    assert pago["external_reference"] == "7"
    assert pago["card"] == {"last_four_digits": "0604"}
    assert pago["payment_method_id"] == "master"
    assert pago["payment_type_id"] == "credit_card"
    assert pago["currency_id"] == "ARS"
    assert pago["preference_id"] == pref["id"]


def test_un_pago_inexistente_no_se_encuentra(simulador):
    assert simulador.obtener_pago(999) is None


def test_los_ids_de_pago_son_numeros_correlativos(simulador):
    pref = preferencia(simulador)

    primero = simulador.pagar(pref["id"], "OTHE", "visa", "3704")
    segundo = simulador.pagar(pref["id"], "APRO", "visa", "3704")

    assert isinstance(primero["id"], int)
    assert segundo["id"] == primero["id"] + 1
    assert simulador.pagos_de_preferencia(pref["id"]) == [primero, segundo]


def test_una_preferencia_aprobada_no_acepta_otro_pago(simulador):
    pref = preferencia(simulador)
    simulador.pagar(pref["id"], "APRO", "master", "0604")

    with pytest.raises(PreferenciaYaPagadaError):
        simulador.pagar(pref["id"], "APRO", "master", "0604")

    assert len(simulador.pagos_de_preferencia(pref["id"])) == 1


def test_despues_de_un_rechazo_se_puede_volver_a_pagar(simulador):
    pref = preferencia(simulador)
    simulador.pagar(pref["id"], "OTHE", "master", "0604")

    pago = simulador.pagar(pref["id"], "APRO", "master", "0604")

    assert pago["status"] == "approved"


def test_pagar_una_preferencia_inexistente_es_un_error(simulador):
    with pytest.raises(PreferenciaInexistenteError):
        simulador.pagar("no-existe", "APRO", "master", "0604")


@pytest.mark.parametrize(
    "titular, back_url, estado",
    [
        ("APRO", "http://sitio/ok", "approved"),
        ("OTHE", "http://sitio/mal", "rejected"),
        ("CONT", "http://sitio/pend", "pending"),
    ],
)
def test_la_url_de_vuelta_usa_la_back_url_del_resultado(
    simulador, titular, back_url, estado
):
    pref = preferencia(simulador)
    pago = simulador.pagar(pref["id"], titular, "master", "0604")

    url = simulador.url_de_vuelta(pago["id"])

    parametros = parse_qs(urlsplit(url).query)
    assert url.startswith(back_url + "?")
    assert parametros["payment_id"] == [str(pago["id"])]
    assert parametros["collection_id"] == [str(pago["id"])]
    assert parametros["status"] == [estado]
    assert parametros["collection_status"] == [estado]
    assert parametros["external_reference"] == ["7"]
    assert parametros["preference_id"] == [pref["id"]]
    assert parametros["payment_type"] == ["credit_card"]
    assert parametros["merchant_order_id"] == [str(pago["merchant_order_id"])]
    assert parametros["site_id"] == ["MLA"]
    assert parametros["processing_mode"] == ["aggregator"]


def test_preferencias_creadas_las_lista_en_orden(simulador):
    primera = preferencia(simulador)
    segunda = preferencia(simulador, external_reference="8")

    ids = [pref["id"] for pref in simulador.preferencias_creadas()]

    assert ids == [primera["id"], segunda["id"]]
