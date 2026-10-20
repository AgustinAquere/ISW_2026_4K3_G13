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


# Versión HTML del mail, con la estética de la pantalla de confirmación
# del sitio (paleta y logo del parque). La versión de texto se mantiene
# para los clientes de correo que no muestran HTML.


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


def test_el_mail_html_no_lleva_imagenes_y_muestra_el_nombre_del_parque(
    servidor,
):
    # El logo como imagen dentro del mail aparecía en Gmail como
    # adjunto: el encabezado lleva solo el nombre del parque.
    notificador(servidor).enviar_confirmacion(compra_nueva())

    mensaje = mail_enviado(servidor)
    html = html_del_mail(servidor)
    assert "EcoHarmony Park" in html
    assert "<img" not in html
    assert not [
        parte
        for parte in mensaje.walk()
        if parte.get_content_maintype() == "image"
    ]


# Medio de pago y detalle de la compra: una fila por entrada, con la
# edad y el precio de cada una, y el total al final. compra_nueva():
# pase regular, edades 40 (precio completo) y 8 (50 %), total $15.000.


@pytest.mark.parametrize(
    "cambios, medio",
    [
        ({}, "Tarjeta (Mercado Pago)"),
        ({"medio_pago": MedioPago.EFECTIVO}, "Efectivo (en boletería)"),
        ({"edades": [1, 3], "total": 0}, "Sin pago (compra sin costo)"),
    ],
    ids=["tarjeta", "efectivo", "sin-costo"],
)
def test_el_mail_informa_el_medio_de_pago(servidor, cambios, medio):
    notificador(servidor).enviar_confirmacion(compra_nueva(**cambios))

    assert ">Medio de pago<" in html_del_mail(servidor)
    assert f">{medio}<" in html_del_mail(servidor)
    assert f"Medio de pago: {medio}" in texto_del_mail(servidor)


def test_el_mail_detalla_cada_entrada_con_su_edad_y_precio(servidor):
    notificador(servidor).enviar_confirmacion(compra_nueva())

    html = html_del_mail(servidor)
    assert ">Detalle de la compra<" in html
    primera = html.index(">Entrada 1<")
    segunda = html.index(">Entrada 2<")
    total = html.index(">Total pagado<")
    assert primera < segunda < total
    assert ">40 años<" in html[primera:segunda]
    assert ">$10.000<" in html[primera:segunda]
    assert ">8 años<" in html[segunda:total]
    assert ">$5.000<" in html[segunda:total]
    assert ">$15.000<" in html[total:]


def test_una_entrada_sin_costo_figura_como_gratis(servidor):
    notificador(servidor).enviar_confirmacion(
        compra_nueva(edades=[1, 3], total=0)
    )

    html = html_del_mail(servidor)
    assert html.count(">Gratis<") == 2
    assert ">1 año<" in html


def test_el_texto_del_mail_detalla_cada_entrada(servidor):
    notificador(servidor).enviar_confirmacion(compra_nueva())

    texto = texto_del_mail(servidor)
    assert "Entrada 1: 40 años, $10.000" in texto
    assert "Entrada 2: 8 años, $5.000" in texto
