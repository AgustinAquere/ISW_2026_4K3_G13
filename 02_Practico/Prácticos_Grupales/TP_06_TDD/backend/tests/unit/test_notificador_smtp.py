import logging
import smtplib

import pytest

from app.adaptadores.notificador import NotificadorSMTP
from app.dominio.modelos import Compra, MedioPago, TipoPase
from tests.fechas import FECHA_VISITA, dd_mm_aaaa

URL_PAGO = "https://sandbox.mercadopago.com.ar/checkout?pref_id=1"


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
        "url_pago": URL_PAGO,
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


def test_el_mail_informa_cantidad_fecha_total_y_link_de_pago(servidor):
    notificador(servidor).enviar_confirmacion(compra_nueva())

    cuerpo = mail_enviado(servidor).get_content()
    resumen = f"Compraste 2 entradas para el {dd_mm_aaaa(FECHA_VISITA)}"
    assert resumen in cuerpo
    assert "$15.000" in cuerpo
    assert URL_PAGO in cuerpo


def test_el_mail_de_pago_en_boleteria_no_incluye_link_de_pago(servidor):
    notificador(servidor).enviar_confirmacion(
        compra_nueva(medio_pago=MedioPago.EFECTIVO, url_pago=None)
    )

    cuerpo = mail_enviado(servidor).get_content()
    assert "boletería" in cuerpo
    assert "mercadopago" not in cuerpo


def test_si_el_mail_no_se_puede_enviar_la_compra_no_falla(caplog):
    def servidor_caido(host, puerto, timeout):
        raise smtplib.SMTPConnectError(421, "servidor no disponible")

    with caplog.at_level(logging.ERROR):
        notificador(servidor_caido).enviar_confirmacion(compra_nueva())

    assert "No se pudo enviar el mail" in caplog.text
