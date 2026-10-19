"""API del Mercado Pago simulado, con el mismo contrato que la real.

La usan dos entradas: un transporte de httpx dentro del mismo proceso (para
PasarelaMercadoPago) y el router HTTP (para /docs y curl).
"""

import json
import re

import httpx

from app.mercado_pago_simulado.nucleo import TOKEN_SIMULADO

PREFIJO_API_SIMULADA = "/mercadopago-simulado/api"

NO_AUTORIZADO = {
    "message": "invalid access token",
    "error": "unauthorized",
    "status": 401,
}
PAGO_NO_ENCONTRADO = {
    "message": "Payment not found",
    "error": "not_found",
    "status": 404,
}
RECURSO_NO_ENCONTRADO = {
    "message": "resource not found",
    "error": "not_found",
    "status": 404,
}
CAMINO_PAGO = re.compile(r"/v1/payments/([^/]+)")


def responder_api(simulador, metodo, camino, autorizacion, cuerpo):
    if autorizacion != f"Bearer {TOKEN_SIMULADO}":
        return 401, NO_AUTORIZADO
    if metodo == "POST" and camino == "/checkout/preferences":
        return 201, simulador.crear_preferencia(cuerpo)
    pago = CAMINO_PAGO.fullmatch(camino)
    if metodo == "GET" and pago:
        id_pago = pago.group(1)
        encontrado = (
            simulador.obtener_pago(int(id_pago)) if id_pago.isdigit() else None
        )
        if encontrado is None:
            return 404, PAGO_NO_ENCONTRADO
        return 200, encontrado
    return 404, RECURSO_NO_ENCONTRADO


def transporte_en_proceso(simulador):
    def atender(solicitud):
        camino = solicitud.url.path.removeprefix(PREFIJO_API_SIMULADA)
        cuerpo = json.loads(solicitud.content) if solicitud.content else None
        estado, respuesta = responder_api(
            simulador,
            solicitud.method,
            camino,
            solicitud.headers.get("Authorization"),
            cuerpo,
        )
        return httpx.Response(estado, json=respuesta)

    return httpx.MockTransport(atender)
