from datetime import date

from pydantic import BaseModel

from app.dominio.modelos import MedioPago, TipoPase


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
            mensaje=compra.resumen(),
        )
