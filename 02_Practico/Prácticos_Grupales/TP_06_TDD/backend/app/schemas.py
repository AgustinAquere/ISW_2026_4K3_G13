from datetime import date
from typing import Annotated

from pydantic import BaseModel, Field

from app.dominio.modelos import EstadoCompra, MedioPago, TipoPase


class CompraRequest(BaseModel):
    fecha_visita: date
    cantidad: int
    edades: list[int]
    tipo_pase: TipoPase
    medio_pago: MedioPago


class CompraResponse(BaseModel):
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


class CotizacionRequest(BaseModel):
    edades: list[Annotated[int, Field(ge=0)]]
    tipo_pase: TipoPase


class CotizacionResponse(BaseModel):
    total: int


class FechasDisponiblesResponse(BaseModel):
    fechas: list[date]
