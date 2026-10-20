"""Pasarela de pago con Mercado Pago Checkout Pro (API REST)."""

import httpx

from app.dominio.errores import PagoNoDisponibleError
from app.dominio.modelos import PagoInformado

URL_API_MERCADO_PAGO = "https://api.mercadopago.com"
URL_PREFERENCIAS_MERCADO_PAGO = f"{URL_API_MERCADO_PAGO}/checkout/preferences"
URL_PAGOS_MERCADO_PAGO = f"{URL_API_MERCADO_PAGO}/v1/payments"


class PasarelaMercadoPago:
    """Crea una preferencia de Checkout Pro y devuelve la URL de pago.

    url_api permite hablarle al Mercado Pago simulado con el mismo código.
    """

    def __init__(
        self,
        access_token,
        url_retorno,
        cliente=None,
        url_api=URL_API_MERCADO_PAGO,
        email_comprador_prueba=None,
    ):
        """Recibe las credenciales y la URL a la que vuelve el pago.

        email_comprador_prueba completa el email del checkout en modo
        prueba.
        """
        self._access_token = access_token
        self._url_retorno = url_retorno
        self._cliente = cliente or httpx.Client(timeout=10)
        self._url_api = url_api
        self._email_comprador_prueba = email_comprador_prueba

    def _cabeceras(self):
        return {"Authorization": f"Bearer {self._access_token}"}

    def crear_pago(self, compra):
        """Crea la preferencia de pago y devuelve el link del checkout."""
        palabra = "entrada" if compra.cantidad == 1 else "entradas"
        preferencia = {
            "items": [
                {
                    "title": f"EcoHarmony Park: {compra.cantidad} {palabra} "
                    f"{compra.tipo_pase.value} para el "
                    f"{_fecha_con_palabras(compra.fecha_visita)}",
                    "quantity": 1,
                    "unit_price": compra.total,
                    "currency_id": "ARS",
                }
            ],
            "external_reference": compra.referencia_externa(),
            "back_urls": dict.fromkeys(
                ("success", "failure", "pending"), self._url_retorno
            ),
        }
        if self._url_retorno.startswith("https://"):
            preferencia["auto_return"] = "approved"
        if self._email_comprador_prueba:
            # En modo prueba solo paga un comprador de prueba: el checkout
            # trae su email completado.
            preferencia["payer"] = {"email": self._email_comprador_prueba}
        try:
            respuesta = self._cliente.post(
                f"{self._url_api}/checkout/preferences",
                json=preferencia,
                headers=self._cabeceras(),
            )
            respuesta.raise_for_status()
        except httpx.HTTPError as error:
            raise PagoNoDisponibleError() from error
        datos = respuesta.json()
        # Las credenciales de prueba solo funcionan en el checkout de prueba.
        if self._access_token.startswith("TEST-"):
            return datos["sandbox_init_point"]
        return datos["init_point"]

    def consultar_pago(self, id_pago):
        """Consulta un pago por su id; uno no numérico no está aprobado."""
        if not id_pago.isdigit():
            return PagoInformado(id_pago, False, None, 0)
        try:
            respuesta = self._cliente.get(
                f"{self._url_api}/v1/payments/{id_pago}",
                headers=self._cabeceras(),
            )
            respuesta.raise_for_status()
        except httpx.HTTPError as error:
            raise PagoNoDisponibleError() from error
        return _pago_informado(respuesta.json())

    def buscar_pago(self, referencia):
        """Busca el pago de la compra por su referencia.

        Si el checkout se abrió en otra pestaña, el sitio no recibe el id
        del pago: lo busca por la referencia de la compra
        (external_reference). Prefiere un pago aprobado y devuelve None
        si no hay pagos.
        """
        try:
            respuesta = self._cliente.get(
                f"{self._url_api}/v1/payments/search",
                params={
                    "external_reference": referencia,
                    "sort": "date_created",
                    "criteria": "desc",
                },
                headers=self._cabeceras(),
            )
            respuesta.raise_for_status()
        except httpx.HTTPError as error:
            raise PagoNoDisponibleError() from error
        pagos = respuesta.json()["results"]
        if not pagos:
            return None
        aprobados = [pago for pago in pagos if pago["status"] == "approved"]
        return _pago_informado((aprobados or pagos)[0])


# Mercado Pago le quita las barras al título: "20/10/2026" se ve
# "20102026", así que la fecha va con palabras.
MESES = (
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
)


def _fecha_con_palabras(fecha):
    return f"{fecha.day} de {MESES[fecha.month - 1]} de {fecha.year}"


def _pago_informado(datos):
    return PagoInformado(
        id_pago=str(datos["id"]),
        aprobado=datos["status"] == "approved",
        referencia=datos.get("external_reference"),
        monto=round(datos["transaction_amount"]),
        rechazado=datos["status"] == "rejected",
    )
