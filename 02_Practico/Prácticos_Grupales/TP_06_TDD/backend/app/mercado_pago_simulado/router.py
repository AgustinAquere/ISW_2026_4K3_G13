"""Endpoints del Mercado Pago simulado: su API y el checkout."""

import json
from pathlib import Path
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from app.dependencias import obtener_mercado_pago_simulado
from app.mercado_pago_simulado.api import responder_api
from app.mercado_pago_simulado.nucleo import (
    MercadoPagoSimulado,
    PreferenciaInexistenteError,
    PreferenciaYaPagadaError,
)

PAGINA_CHECKOUT = (
    Path(__file__).resolve().parent.parent
    / "static"
    / "mercadopago-simulado"
    / "checkout.html"
)

router = APIRouter(
    prefix="/mercadopago-simulado", tags=["Mercado Pago simulado"]
)
Simulador = Annotated[
    MercadoPagoSimulado, Depends(obtener_mercado_pago_simulado)
]


class PagoCheckoutRequest(BaseModel):
    """Pago que envía la página del checkout simulado.

    El número de tarjeta, el código y el vencimiento no salen del
    navegador: si llegan, la solicitud se rechaza.
    """

    model_config = ConfigDict(extra="forbid")

    titular: str = Field(min_length=1)
    marca: Literal["visa", "master", "amex"]
    ultimos_digitos: str = Field(pattern=r"^\d{4}$")


@router.api_route("/api/{camino:path}", methods=["GET", "POST"])
async def api_simulada(camino: str, request: Request, simulador: Simulador):
    """Atiende la API simulada por HTTP, para /docs y curl."""
    contenido = await request.body()
    estado, respuesta = responder_api(
        simulador,
        request.method,
        f"/{camino}",
        request.headers.get("Authorization"),
        json.loads(contenido) if contenido else None,
        dict(request.query_params),
    )
    return JSONResponse(respuesta, status_code=estado)


@router.get("/checkout", include_in_schema=False)
def pagina_de_checkout():
    """Devuelve la página del checkout simulado."""
    return FileResponse(PAGINA_CHECKOUT)


@router.get("/checkout/{id_preferencia}/datos")
def datos_del_checkout(id_preferencia: str, simulador: Simulador):
    """Devuelve la descripción, el total y si ya se pagó."""
    preferencia = simulador.obtener_preferencia(id_preferencia)
    if preferencia is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Preferencia inexistente"
        )
    return {
        "descripcion": preferencia["items"][0]["title"],
        "total": simulador.total(id_preferencia),
        "pagada": simulador.esta_pagada(id_preferencia),
    }


@router.post(
    "/checkout/{id_preferencia}/pagos", status_code=status.HTTP_201_CREATED
)
def pagar_desde_el_checkout(
    id_preferencia: str, pago: PagoCheckoutRequest, simulador: Simulador
):
    """Paga la preferencia y devuelve la URL de vuelta al sitio."""
    try:
        creado = simulador.pagar(
            id_preferencia, pago.titular, pago.marca, pago.ultimos_digitos
        )
    except PreferenciaInexistenteError as error:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Preferencia inexistente"
        ) from error
    except PreferenciaYaPagadaError as error:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Este pago ya fue realizado"
        ) from error
    preferencia = simulador.obtener_preferencia(id_preferencia)
    return {
        "pago": creado,
        "url_de_vuelta": simulador.url_de_vuelta(creado["id"]),
        "volver_automaticamente": preferencia.get("auto_return") == "approved"
        and creado["status"] == "approved",
    }
