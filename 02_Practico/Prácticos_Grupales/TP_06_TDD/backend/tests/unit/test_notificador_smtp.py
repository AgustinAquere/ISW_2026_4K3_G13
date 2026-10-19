import logging
import smtplib

import pytest

from app.adaptadores.notificador import NotificadorSMTP
from app.dominio.modelos import Compra, MedioPago, TipoPase
from tests.fechas import FECHA_VISITA, dd_mm_aaaa


def compra_nueva(**cambios):
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


class ServidorSMTPFalso:
    """Imita smtplib.SMTP y guarda lo que se le pidió."""

    instancias = []

    def __init__(self, host, puerto, timeout):
        self.conexion = (host, puerto)
        self.tls = False
        self.credenciales = None
        self.enviados = []
        ServidorSMTPFalso.instancias.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *excepcion):
        return False

    def starttls(self):
        self.tls = True

    def login(self, usuario, contrasena):
        self.credenciales = (usuario, contrasena)

    def send_message(self, mensaje):
        self.enviados.append(mensaje)


@pytest.fixture
def servidor():
    ServidorSMTPFalso.instancias = []
    yield ServidorSMTPFalso
    ServidorSMTPFalso.instancias = []


def notificador(smtp):
    return NotificadorSMTP(
        host="smtp.ejemplo.com",
        puerto=587,
        usuario="parque@ejemplo.com",
        contrasena="secreta",
        remitente="EcoHarmony Park <parque@ejemplo.com>",
        logger=logging.getLogger("test"),
        smtp=smtp,
    )


def mail_enviado(servidor):
    (instancia,) = servidor.instancias
    (mensaje,) = instancia.enviados
    return mensaje


def texto_del_mail(servidor):
    return mail_enviado(servidor).get_body(("plain",)).get_content()


def html_del_mail(servidor):
    return mail_enviado(servidor).get_body(("html",)).get_content()


def test_envia_el_mail_al_usuario_que_compro(servidor):
    notificador(servidor).enviar_confirmacion(compra_nueva())

    mensaje = mail_enviado(servidor)
    assert mensaje["To"] == "visitante@ecoharmony.com"
    assert mensaje["From"] == "EcoHarmony Park <parque@ejemplo.com>"
    assert "Confirmación de compra" in mensaje["Subject"]


def test_se_conecta_con_tls_y_las_credenciales_configuradas(servidor):
    notificador(servidor).enviar_confirmacion(compra_nueva())

    (instancia,) = servidor.instancias
    assert instancia.conexion == ("smtp.ejemplo.com", 587)
    assert instancia.tls
    assert instancia.credenciales == ("parque@ejemplo.com", "secreta")


def test_el_mail_informa_numero_cantidad_fecha_y_total(servidor):
    notificador(servidor).enviar_confirmacion(compra_nueva())

    cuerpo = texto_del_mail(servidor)
    assert "Compra n.º 7" in cuerpo
    resumen = f"Compraste 2 entradas para el {dd_mm_aaaa(FECHA_VISITA)}"
    assert resumen in cuerpo
    assert "$15.000" in cuerpo


def test_el_mail_de_pago_con_tarjeta_informa_el_pago_aprobado(servidor):
    # Con tarjeta, el mail se envía cuando Mercado Pago aprueba el pago.
    notificador(servidor).enviar_confirmacion(compra_nueva())

    cuerpo = texto_del_mail(servidor)
    assert "Pago aprobado con Mercado Pago" in cuerpo
    assert "Completá el pago" not in cuerpo


def test_el_mail_de_una_compra_sin_costo_no_pide_pagar(servidor):
    notificador(servidor).enviar_confirmacion(
        compra_nueva(edades=[1, 3], total=0)
    )

    cuerpo = texto_del_mail(servidor)
    assert "no tiene costo" in cuerpo
    assert "Mercado Pago" not in cuerpo


def test_el_mail_de_pago_en_boleteria_no_incluye_link_de_pago(servidor):
    notificador(servidor).enviar_confirmacion(
        compra_nueva(medio_pago=MedioPago.EFECTIVO)
    )

    cuerpo = texto_del_mail(servidor)
    assert "boletería" in cuerpo
    assert "mercadopago" not in cuerpo


def test_si_el_mail_no_se_puede_enviar_la_compra_no_falla(caplog):
    def servidor_caido(host, puerto, timeout):
        raise smtplib.SMTPConnectError(421, "servidor no disponible")

    with caplog.at_level(logging.ERROR):
        notificador(servidor_caido).enviar_confirmacion(compra_nueva())

    assert "No se pudo enviar el mail" in caplog.text


# Versión HTML del mail, con la estética de la pantalla de confirmación del
# sitio (paleta y logo del parque). La versión de texto se mantiene para los
# clientes de correo que no muestran HTML.


def test_el_mail_tiene_una_version_html_con_el_resumen_de_la_compra(servidor):
    notificador(servidor).enviar_confirmacion(compra_nueva())

    html = html_del_mail(servidor)
    assert f"Compraste 2 entradas para el {dd_mm_aaaa(FECHA_VISITA)}" in html
    assert "Compra n.º" in html
    assert ">7<" in html
    assert "$15.000" in html
    assert "Tus entradas se verifican al ingresar al parque" in html


@pytest.mark.parametrize(
    "cambios, titulo, etiqueta_total",
    [
        ({}, "¡Pago aprobado!", "Total pagado"),
        (
            {"medio_pago": MedioPago.EFECTIVO},
            "¡Compra confirmada!",
            "Total a pagar",
        ),
        ({"edades": [1, 3], "total": 0}, "¡Compra confirmada!", "Total"),
    ],
    ids=["tarjeta", "efectivo", "sin-costo"],
)
def test_el_titulo_del_mail_html_depende_del_pago(
    servidor, cambios, titulo, etiqueta_total
):
    notificador(servidor).enviar_confirmacion(compra_nueva(**cambios))

    html = html_del_mail(servidor)
    assert titulo in html
    assert f">{etiqueta_total}<" in html


def test_el_mail_html_de_efectivo_avisa_que_se_paga_en_boleteria(servidor):
    notificador(servidor).enviar_confirmacion(
        compra_nueva(medio_pago=MedioPago.EFECTIVO)
    )

    assert "boletería" in html_del_mail(servidor)


def test_el_mail_html_usa_la_paleta_del_sitio(servidor):
    notificador(servidor).enviar_confirmacion(compra_nueva())

    html = html_del_mail(servidor)
    assert "#386641" in html  # verde oscuro
    assert "#f2e8cf" in html  # crema


def test_el_mail_html_muestra_el_logo_del_parque_como_imagen_adjunta(
    servidor,
):
    # Gmail no muestra SVG: el logo va como PNG dentro del mail (cid).
    notificador(servidor).enviar_confirmacion(compra_nueva())

    mensaje = mail_enviado(servidor)
    (logo,) = [
        parte
        for parte in mensaje.walk()
        if parte.get_content_type() == "image/png"
    ]
    content_id = logo["Content-ID"].strip("<>")
    assert f'src="cid:{content_id}"' in html_del_mail(servidor)
    assert logo.get_content().startswith(b"\x89PNG")


def test_el_logo_va_dentro_del_mensaje_y_no_como_adjunto(servidor):
    # Con Content-Disposition: attachment, Gmail lo muestra como archivo
    # adjunto debajo del mail y no dentro del HTML.
    notificador(servidor).enviar_confirmacion(compra_nueva())

    (logo,) = [
        parte
        for parte in mail_enviado(servidor).walk()
        if parte.get_content_type() == "image/png"
    ]
    assert logo.get_content_disposition() == "inline"
