import smtplib
from email.message import EmailMessage

from app.dominio.modelos import MedioPago


class NotificadorEnMemoria:
    """Doble de prueba: registra los mails en lugar de enviarlos."""

    def __init__(self):
        self.enviados = []

    def enviar_confirmacion(self, compra):
        self.enviados.append(compra)


class NotificadorEmailLog:
    """Simula el envío del mail de confirmación escribiéndolo en el log."""

    def __init__(self, logger):
        self._logger = logger

    def enviar_confirmacion(self, compra):
        self._logger.info(
            "Mail de confirmación a %s: %s",
            compra.email_usuario,
            compra.resumen(),
        )


class NotificadorSMTP:
    """Envía el mail de confirmación por SMTP con STARTTLS."""

    def __init__(
        self,
        host,
        puerto,
        usuario,
        contrasena,
        remitente,
        logger,
        smtp=smtplib.SMTP,
    ):
        self._host = host
        self._puerto = puerto
        self._usuario = usuario
        self._contrasena = contrasena
        self._remitente = remitente
        self._logger = logger
        self._smtp = smtp

    def enviar_confirmacion(self, compra):
        mensaje = EmailMessage()
        mensaje["From"] = self._remitente
        mensaje["To"] = compra.email_usuario
        mensaje["Subject"] = "EcoHarmony Park: Confirmación de compra"
        mensaje.set_content(_cuerpo_del_mail(compra))
        try:
            with self._smtp(self._host, self._puerto, timeout=10) as servidor:
                servidor.starttls()
                servidor.login(self._usuario, self._contrasena)
                servidor.send_message(mensaje)
        except OSError:
            # La compra ya está registrada: un mail fallido no debe anularla.
            self._logger.exception(
                "No se pudo enviar el mail de confirmación a %s",
                compra.email_usuario,
            )


def _cuerpo_del_mail(compra):
    total = f"${compra.total:,}".replace(",", ".")
    if compra.total == 0:
        pago = "Tu compra no tiene costo."
    elif compra.medio_pago == MedioPago.TARJETA:
        pago = "Pago aprobado con Mercado Pago."
    else:
        pago = "Pagás en la boletería del parque el día de la visita."
    return (
        f"¡Gracias por tu compra!\n\n"
        f"Compra n.º {compra.id}\n"
        f"{compra.resumen()}.\n"
        f"Pase: {compra.tipo_pase.value}\n"
        f"Total: {total}\n"
        f"{pago}\n\n"
        f"Tus entradas se verifican al ingresar al parque.\n"
        f"EcoHarmony Park"
    )
