"""Esquemas de entrada y salida de la API."""

from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from app.dominio.modelos import EstadoCompra, MedioPago, TipoPase
from app.servicios.compra_service import EDAD_MAXIMA


class CompraRequest(BaseModel):
    """Datos de la compra que envía el front."""

    fecha_visita: date
    cantidad: int
    edades: list[int]
    tipo_pase: TipoPase
    medio_pago: MedioPago


class CompraResponse(BaseModel):
    """Compra registrada, con el mensaje para el visitante."""

    id: int
    fecha_visita: date
    cantidad: int
    tipo_pase: TipoPase
    medio_pago: MedioPago
    total: int
    url_pago: str | None
    estado: EstadoCompra
    mensaje: str

    @classmethod
    def desde_compra(cls, compra):
        """Arma la respuesta a partir de una compra del dominio."""
        return cls(
            id=compra.id,
            fecha_visita=compra.fecha_visita,
            cantidad=compra.cantidad,
            tipo_pase=compra.tipo_pase,
            medio_pago=compra.medio_pago,
            total=compra.total,
            url_pago=compra.url_pago,
            estado=compra.estado,
            mensaje=compra.resumen(),
        )


class VerificacionPagoResponse(CompraResponse):
    """Compra y estado de su pago en Mercado Pago."""

    pago: Literal["aprobado", "rechazado", "pendiente", "sin_pago"]

    @classmethod
    def desde_verificacion(cls, compra, pago):
        """Arma la respuesta con la compra y el pago (o None)."""
        if compra.estado == EstadoCompra.CONFIRMADA:
            estado_del_pago = "aprobado"
        elif pago is None:
            estado_del_pago = "sin_pago"
        elif pago.rechazado:
            estado_del_pago = "rechazado"
        else:
            estado_del_pago = "pendiente"
        return cls(
            **CompraResponse.desde_compra(compra).model_dump(),
            pago=estado_del_pago,
        )


class ConfirmacionPagoRequest(BaseModel):
    """Id del pago que informa Mercado Pago al volver."""

    id_pago: str


class CotizacionRequest(BaseModel):
    """Edades y pase para calcular el total."""

    edades: list[Annotated[int, Field(ge=0, le=EDAD_MAXIMA)]]
    tipo_pase: TipoPase


class CotizacionResponse(BaseModel):
    """Total en pesos."""

    total: int


class FechasDisponiblesResponse(BaseModel):
    """Fechas en que se pueden comprar entradas."""

    fechas: list[date]
