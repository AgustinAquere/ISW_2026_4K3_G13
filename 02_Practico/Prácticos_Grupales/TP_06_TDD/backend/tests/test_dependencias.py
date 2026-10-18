from app.adaptadores.notificador import NotificadorEmailLog, NotificadorSMTP
from app.adaptadores.pasarela_pago import (
    PasarelaMercadoPago,
    PasarelaMercadoPagoSimulada,
)
from app.dependencias import (
    crear_notificador,
    crear_pasarela_pago,
    usuarios_registrados,
)

CONFIGURACION_SMTP = {
    "SMTP_HOST": "smtp.ejemplo.com",
    "SMTP_PUERTO": "587",
    "SMTP_USUARIO": "parque@ejemplo.com",
    "SMTP_CONTRASENA": "secreta",
}


def test_con_access_token_se_usa_mercado_pago():
    pasarela = crear_pasarela_pago({"MP_ACCESS_TOKEN": "TEST-123"})

    assert isinstance(pasarela, PasarelaMercadoPago)


def test_sin_access_token_se_simula_mercado_pago():
    assert isinstance(crear_pasarela_pago({}), PasarelaMercadoPagoSimulada)


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
