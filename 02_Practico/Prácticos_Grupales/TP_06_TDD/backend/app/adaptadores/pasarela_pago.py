from urllib.parse import urlencode

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
    ):
        self._access_token = access_token
        self._url_retorno = url_retorno
        self._cliente = cliente or httpx.Client(timeout=10)
        self._url_api = url_api

    def _cabeceras(self):
        return {"Authorization": f"Bearer {self._access_token}"}

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
        if self._url_retorno.startswith("https://"):
            preferencia["auto_return"] = "approved"
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
        datos = respuesta.json()
        referencia = datos.get("external_reference")
        return PagoInformado(
            id_pago=id_pago,
            aprobado=datos["status"] == "approved",
            id_compra=int(referencia) if referencia else None,
            monto=round(datos["transaction_amount"]),
        )


class PasarelaMercadoPagoSimulada:
    """Simula Mercado Pago: el pago vuelve al sitio aprobado (FAQ 4)."""

    def __init__(self, url_retorno="/"):
        self._url_retorno = url_retorno
        self.pagos_creados = []

    def crear_pago(self, compra):
        self.pagos_creados.append(compra)
        parametros = {
            "collection_status": "approved",
            "payment_id": f"SIMULADO-{compra.id}",
            "external_reference": compra.id,
        }
        return f"{self._url_retorno}?{urlencode(parametros)}"

    def consultar_pago(self, id_pago):
        for compra in self.pagos_creados:
            if id_pago == f"SIMULADO-{compra.id}":
                return PagoInformado(id_pago, True, compra.id, compra.total)
        return PagoInformado(id_pago, False, None, 0)
