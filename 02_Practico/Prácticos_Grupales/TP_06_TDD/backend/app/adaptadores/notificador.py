"""Envío del mail de confirmación de la compra."""

import smtplib
from email.message import EmailMessage
from html import escape
from pathlib import Path
from string import Template

from app.dominio.modelos import MedioPago
from app.dominio.precios import calcular_precio_entrada

RUTA_APP = Path(__file__).resolve().parent.parent
PLANTILLA_HTML = RUTA_APP / "plantillas" / "mail_confirmacion.html"


class NotificadorEnMemoria:
    """Doble de prueba: registra los mails en lugar de enviarlos."""

    def __init__(self):
        """Empieza sin mails enviados."""
        self.enviados = []

    def enviar_confirmacion(self, compra):
        """Registra la compra en lugar de enviar el mail."""
        self.enviados.append(compra)


class NotificadorEmailLog:
    """Simula el envío del mail de confirmación escribiéndolo en el log."""

    def __init__(self, logger):
        """Recibe el logger donde se escriben los mails."""
        self._logger = logger

    def enviar_confirmacion(self, compra):
        """Escribe en el log el destinatario y el resumen de la compra."""
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
        """Recibe el servidor, las credenciales y el remitente.

        smtp permite reemplazar smtplib.SMTP en las pruebas.
        """
        self._host = host
        self._puerto = puerto
        self._usuario = usuario
        self._contrasena = contrasena
        self._remitente = remitente
        self._logger = logger
        self._smtp = smtp

    def enviar_confirmacion(self, compra):
        """Envía el mail en texto y en HTML; si falla, lo deja en el log."""
        mensaje = EmailMessage()
        mensaje["From"] = self._remitente
        mensaje["To"] = compra.email_usuario
        mensaje["Subject"] = "EcoHarmony Park: Confirmación de compra"
        mensaje.set_content(_cuerpo_del_mail(compra))
        mensaje.add_alternative(_cuerpo_html(compra), subtype="html")
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
    _, etiqueta_total, _ = _datos_del_pago(compra)
    entradas = "".join(
        f"Entrada {numero}: {_edad(edad)}, {_precio(precio)}\n"
        for numero, edad, precio in _entradas(compra)
    )
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
        f"Medio de pago: {_medio_de_pago(compra)}\n\n"
        f"Detalle de la compra:\n"
        f"{entradas}"
        f"{etiqueta_total}: {_pesos(compra.total)}\n\n"
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


def _medio_de_pago(compra):
    if compra.total == 0:
        # Con tarjeta y sin costo no se pasa por Mercado Pago.
        return "Sin pago (compra sin costo)"
    if compra.medio_pago == MedioPago.TARJETA:
        return "Tarjeta (Mercado Pago)"
    return "Efectivo (en boletería)"


def _entradas(compra):
    """Número, edad y precio de cada entrada, con los precios del dominio."""
    return [
        (numero, edad, calcular_precio_entrada(edad, compra.tipo_pase))
        for numero, edad in enumerate(compra.edades, start=1)
    ]


def _pesos(monto):
    return f"${monto:,}".replace(",", ".")


def _precio(precio):
    return "Gratis" if precio == 0 else _pesos(precio)


def _edad(edad):
    return "1 año" if edad == 1 else f"{edad} años"


ESTILO_CELDA = 'style="padding:8px 0;border-bottom:1px solid #f2e8cf;"'


def _filas_de_entradas(compra):
    return "".join(
        "<tr>"
        f"<td {ESTILO_CELDA}>Entrada {numero}</td>"
        f"<td {ESTILO_CELDA}>{escape(_edad(edad))}</td>"
        f'<td align="right" {ESTILO_CELDA}>{escape(_precio(precio))}</td>'
        "</tr>"
        for numero, edad, precio in _entradas(compra)
    )


def _cuerpo_html(compra):
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
        medio_pago=escape(_medio_de_pago(compra)),
        filas_entradas=_filas_de_entradas(compra),
        etiqueta_total=escape(etiqueta_total),
        total=escape(_pesos(compra.total)),
        bloque_pago=bloque_pago,
    )
