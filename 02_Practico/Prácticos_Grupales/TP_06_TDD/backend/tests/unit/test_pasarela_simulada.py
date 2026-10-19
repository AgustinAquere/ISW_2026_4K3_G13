from datetime import date
from urllib.parse import parse_qs, urlsplit

from app.adaptadores.pasarela_pago import PasarelaMercadoPagoSimulada
from app.dominio.modelos import Compra, MedioPago, PagoInformado, TipoPase

URL_RETORNO = "http://127.0.0.1:8000/"


def compra_con_tarjeta():
    return Compra(
        email_usuario="visitante@ecoharmony.com",
        fecha_visita=date(2026, 11, 15),
        cantidad=2,
        edades=[40, 8],
        tipo_pase=TipoPase.REGULAR,
        medio_pago=MedioPago.TARJETA,
        total=15000,
        id=7,
    )


def test_el_pago_simulado_vuelve_al_sitio_con_el_pago_aprobado():
    url = PasarelaMercadoPagoSimulada(URL_RETORNO).crear_pago(
        compra_con_tarjeta()
    )

    parametros = parse_qs(urlsplit(url).query)
    assert url.startswith(URL_RETORNO)
    assert parametros["collection_status"] == ["approved"]
    assert parametros["external_reference"] == ["7"]
    assert parametros["payment_id"] == ["SIMULADO-7"]


def test_el_pago_simulado_se_informa_aprobado_por_el_total():
    pasarela = PasarelaMercadoPagoSimulada(URL_RETORNO)
    pasarela.crear_pago(compra_con_tarjeta())

    assert pasarela.consultar_pago("SIMULADO-7") == PagoInformado(
        "SIMULADO-7", True, 7, 15000
    )


def test_un_pago_simulado_desconocido_no_esta_aprobado():
    pago = PasarelaMercadoPagoSimulada(URL_RETORNO).consultar_pago("otro")

    assert not pago.aprobado
