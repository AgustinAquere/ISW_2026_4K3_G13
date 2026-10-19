import smtplib
from email.message import EmailMessage
from email.utils import make_msgid
from html import escape
from pathlib import Path
from string import Template

from app.dominio.modelos import MedioPago

RUTA_APP = Path(__file__).resolve().parent.parent
PLANTILLA_HTML = RUTA_APP / "plantillas" / "mail_confirmacion.html"
# Gmail no muestra SVG: el logo del parque va como PNG dentro del mail.
LOGO_PNG = RUTA_APP / "static" / "logo-ecoharmony.png"


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
        cid_logo = make_msgid(domain="ecoharmony.park")
        mensaje.add_alternative(
            _cuerpo_html(compra, cid_logo.strip("<>")), subtype="html"
        )
        mensaje.get_payload()[1].add_related(
            LOGO_PNG.read_bytes(),
            maintype="image",
            subtype="png",
            cid=cid_logo,
            filename="logo-ecoharmony.png",
        )
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


def _datos_del_pago(compra):
    """Título, etiqueta del total y aviso de pago, como en el sitio."""
    if compra.total == 0:
        return "¡Compra confirmada!", "Total", "Tu compra no tiene costo."
    if compra.medio_pago == MedioPago.TARJETA:
        return "¡Pago aprobado!", "Total pagado", ""
    return (
        "¡Compra confirmada!",
        "Total a pagar",
        "Pagás en la boletería del parque el día de tu visita.",
    )


def _cuerpo_html(compra, cid_logo):
    titulo, etiqueta_total, pago = _datos_del_pago(compra)
    bloque_pago = (
        '<p style="margin:16px 0 0;padding:10px 12px;'
        'border-left:4px solid #6a994e;text-align:left;font-weight:700;">'
        f"{escape(pago)}</p>"
        if pago
        else ""
    )
    plantilla = Template(PLANTILLA_HTML.read_text(encoding="utf-8"))
    return plantilla.substitute(
        titulo=escape(titulo),
        resumen=escape(compra.resumen()),
        numero=compra.id,
        pase="VIP" if compra.tipo_pase.value == "VIP" else "Regular",
        etiqueta_total=escape(etiqueta_total),
        total=escape(f"${compra.total:,}".replace(",", ".")),
        bloque_pago=bloque_pago,
        cid_logo=escape(cid_logo),
    )
