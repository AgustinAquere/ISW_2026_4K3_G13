import json

import httpx

from app.adaptadores.notificador import NotificadorEmailLog, NotificadorSMTP
from app.adaptadores.pasarela_pago import PasarelaMercadoPago
from app.dependencias import (
    crear_notificador,
    crear_pasarela_pago,
    usuarios_registrados,
)
from app.dominio.modelos import Compra, MedioPago, TipoPase
from app.mercado_pago_simulado.nucleo import MercadoPagoSimulado
from tests.fechas import FECHA_VISITA

CONFIGURACION_SMTP = {
    "SMTP_HOST": "smtp.ejemplo.com",
    "SMTP_PUERTO": "587",
    "SMTP_USUARIO": "parque@ejemplo.com",
    "SMTP_CONTRASENA": "secreta",
}


def test_con_access_token_se_usa_mercado_pago():
    pasarela = crear_pasarela_pago({"MP_ACCESS_TOKEN": "TEST-123"})

    assert isinstance(pasarela, PasarelaMercadoPago)


def test_sin_access_token_se_usa_el_mercado_pago_simulado():
    simulador = MercadoPagoSimulado("http://127.0.0.1:8000/")
    compra = Compra(
        email_usuario="visitante@ecoharmony.com",
        fecha_visita=FECHA_VISITA,
        cantidad=1,
        edades=[30],
        tipo_pase=TipoPase.REGULAR,
        medio_pago=MedioPago.TARJETA,
        total=10000,
        id=1,
    )

    url = crear_pasarela_pago({}, simulador).crear_pago(compra)

    assert url.startswith(
        "http://127.0.0.1:8000/mercadopago-simulado/checkout?pref_id="
    )
    assert len(simulador.preferencias_creadas()) == 1


def test_con_servidor_smtp_se_envian_mails_reales():
    assert isinstance(crear_notificador(CONFIGURACION_SMTP), NotificadorSMTP)


def test_sin_servidor_smtp_el_mail_se_escribe_en_el_log():
    assert isinstance(crear_notificador({}), NotificadorEmailLog)


def test_los_usuarios_registrados_se_pueden_configurar():
    configuracion = {"USUARIOS_REGISTRADOS": "ana@mail.com, juan@mail.com"}

    assert usuarios_registrados(configuracion) == [
        "ana@mail.com",
        "juan@mail.com",
    ]


def test_sin_configurar_hay_un_usuario_de_demostracion():
    assert usuarios_registrados({}) == ["visitante@ecoharmony.com"]


def test_el_email_del_comprador_de_prueba_se_toma_del_env():
    solicitudes = []

    def api(solicitud):
        solicitudes.append(solicitud)
        return httpx.Response(201, json={"init_point": "x"})

    pasarela = crear_pasarela_pago(
        {
            "MP_ACCESS_TOKEN": "APP_USR-1",
            "MP_EMAIL_COMPRADOR_PRUEBA": "TESTUSER123@testuser.com",
        },
        cliente=httpx.Client(transport=httpx.MockTransport(api)),
    )
    pasarela.crear_pago(
        Compra(
            email_usuario="visitante@ecoharmony.com",
            fecha_visita=FECHA_VISITA,
            cantidad=1,
            edades=[30],
            tipo_pase=TipoPase.REGULAR,
            medio_pago=MedioPago.TARJETA,
            total=10000,
            id=1,
        )
    )

    preferencia = json.loads(solicitudes[0].content)
    assert preferencia["payer"] == {"email": "TESTUSER123@testuser.com"}
