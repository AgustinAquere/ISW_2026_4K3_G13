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
