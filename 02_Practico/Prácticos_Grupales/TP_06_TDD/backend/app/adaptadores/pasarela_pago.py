URL_CHECKOUT_MERCADO_PAGO = (
    "https://www.mercadopago.com.ar/checkout/v1/redirect"
)


class PasarelaMercadoPagoSimulada:
    """Simula la creación de un pago en Mercado Pago y devuelve su URL."""

    def __init__(self):
        self.pagos_creados = []

    def crear_pago(self, compra):
        self.pagos_creados.append(compra)
        return f"{URL_CHECKOUT_MERCADO_PAGO}?pref_id=SIMULADO-{compra.id}"
