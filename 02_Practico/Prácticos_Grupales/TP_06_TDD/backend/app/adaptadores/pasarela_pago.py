import httpx

from app.dominio.errores import PagoNoDisponibleError

URL_CHECKOUT_MERCADO_PAGO = (
    "https://www.mercadopago.com.ar/checkout/v1/redirect"
)
URL_PREFERENCIAS_MERCADO_PAGO = (
    "https://api.mercadopago.com/checkout/preferences"
)


class PasarelaMercadoPago:
    """Crea una preferencia de Checkout Pro y devuelve la URL de pago."""

    def __init__(self, access_token, url_retorno, cliente=None):
        self._access_token = access_token
        self._url_retorno = url_retorno
        self._cliente = cliente or httpx.Client(timeout=10)

    def crear_pago(self, compra):
        palabra = "entrada" if compra.cantidad == 1 else "entradas"
        preferencia = {
            "items": [
                {
                    "title": f"EcoHarmony Park: {compra.cantidad} {palabra} "
                    f"{compra.tipo_pase.value} para el "
                    f"{compra.fecha_visita:%d/%m/%Y}",
                    "quantity": 1,
                    "unit_price": compra.total,
                    "currency_id": "ARS",
                }
            ],
            "external_reference": str(compra.id),
            "back_urls": dict.fromkeys(
                ("success", "failure", "pending"), self._url_retorno
            ),
        }
        try:
            respuesta = self._cliente.post(
                URL_PREFERENCIAS_MERCADO_PAGO,
                json=preferencia,
                headers={"Authorization": f"Bearer {self._access_token}"},
            )
            respuesta.raise_for_status()
        except httpx.HTTPError as error:
            raise PagoNoDisponibleError() from error
        datos = respuesta.json()
        # Las credenciales de prueba solo funcionan en el checkout de prueba.
        if self._access_token.startswith("TEST-"):
            return datos["sandbox_init_point"]
        return datos["init_point"]


class PasarelaMercadoPagoSimulada:
    """Simula la creación de un pago en Mercado Pago y devuelve su URL."""

    def __init__(self):
        self.pagos_creados = []

    def crear_pago(self, compra):
        self.pagos_creados.append(compra)
        return f"{URL_CHECKOUT_MERCADO_PAGO}?pref_id=SIMULADO-{compra.id}"
