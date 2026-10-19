"""Mercado Pago simulado: preferencias y pagos en memoria.

Imita Checkout Pro para hacer la demo sin cuenta de Mercado Pago. El
titular de la tarjeta define el resultado, igual que las tarjetas de prueba
reales.
"""

import uuid
from datetime import datetime
from itertools import count
from urllib.parse import urlencode

TOKEN_SIMULADO = "SIMULADO"
COLLECTOR_ID = "1234567890"

RESULTADOS_POR_TITULAR = {
    "APRO": ("approved", "accredited"),
    "CONT": ("pending", "pending_contingency"),
    "OTHE": ("rejected", "cc_rejected_other_reason"),
    "FUND": ("rejected", "cc_rejected_insufficient_amount"),
    "SECU": ("rejected", "cc_rejected_bad_filled_security_code"),
}
RESULTADO_POR_DEFECTO = ("rejected", "cc_rejected_other_reason")

# Página de vuelta (back_urls) según el estado del pago.
BACK_URL_POR_ESTADO = {
    "approved": "success",
    "rejected": "failure",
    "pending": "pending",
}


class PreferenciaInexistenteError(Exception):
    """La preferencia no existe (por ejemplo, se reinició el servidor)."""


class PreferenciaYaPagadaError(Exception):
    """La preferencia ya tiene un pago aprobado."""


class MercadoPagoSimulado:
    def __init__(self, url_publica):
        self._url_publica = url_publica.rstrip("/") + "/"
        self._preferencias = {}
        self._pagos = {}
        self._ids_de_pago = count(1000000001)
        self._ids_de_orden = count(2000000001)

    def crear_preferencia(self, datos):
        id_preferencia = f"{COLLECTOR_ID}-{uuid.uuid4()}"
        checkout = (
            f"{self._url_publica}mercadopago-simulado/checkout"
            f"?pref_id={id_preferencia}"
        )
        preferencia = {
            **datos,
            "id": id_preferencia,
            "init_point": checkout,
            "sandbox_init_point": checkout,
            "date_created": _ahora(),
        }
        self._preferencias[id_preferencia] = preferencia
        return preferencia

    def obtener_preferencia(self, id_preferencia):
        return self._preferencias.get(id_preferencia)

    def preferencias_creadas(self):
        return list(self._preferencias.values())

    def total(self, id_preferencia):
        preferencia = self._preferencia(id_preferencia)
        return sum(
            item["unit_price"] * item["quantity"]
            for item in preferencia["items"]
        )

    def pagar(self, id_preferencia, titular, marca, ultimos_digitos):
        preferencia = self._preferencia(id_preferencia)
        if self.esta_pagada(id_preferencia):
            raise PreferenciaYaPagadaError()
        estado, detalle = RESULTADOS_POR_TITULAR.get(
            titular.strip().upper(), RESULTADO_POR_DEFECTO
        )
        pago = {
            "id": next(self._ids_de_pago),
            "status": estado,
            "status_detail": detalle,
            "external_reference": preferencia.get("external_reference"),
            "transaction_amount": float(self.total(id_preferencia)),
            "currency_id": "ARS",
            "payment_method_id": marca,
            "payment_type_id": "credit_card",
            "card": {"last_four_digits": ultimos_digitos},
            "preference_id": id_preferencia,
            "merchant_order_id": next(self._ids_de_orden),
            "date_created": _ahora(),
        }
        self._pagos[pago["id"]] = pago
        return pago

    def obtener_pago(self, id_pago):
        return self._pagos.get(id_pago)

    def pagos_de_preferencia(self, id_preferencia):
        return [
            pago
            for pago in self._pagos.values()
            if pago["preference_id"] == id_preferencia
        ]

    def url_de_vuelta(self, id_pago):
        pago = self._pagos[id_pago]
        preferencia = self._preferencias[pago["preference_id"]]
        back_url = preferencia["back_urls"][
            BACK_URL_POR_ESTADO[pago["status"]]
        ]
        parametros = {
            "collection_id": pago["id"],
            "collection_status": pago["status"],
            "payment_id": pago["id"],
            "status": pago["status"],
            "external_reference": pago["external_reference"],
            "payment_type": pago["payment_type_id"],
            "merchant_order_id": pago["merchant_order_id"],
            "preference_id": pago["preference_id"],
            "site_id": "MLA",
            "processing_mode": "aggregator",
        }
        return f"{back_url}?{urlencode(parametros)}"

    def _preferencia(self, id_preferencia):
        preferencia = self._preferencias.get(id_preferencia)
        if preferencia is None:
            raise PreferenciaInexistenteError()
        return preferencia

    def esta_pagada(self, id_preferencia):
        return any(
            pago["status"] == "approved"
            for pago in self.pagos_de_preferencia(id_preferencia)
        )


def _ahora():
    return datetime.now().astimezone().isoformat(timespec="milliseconds")
