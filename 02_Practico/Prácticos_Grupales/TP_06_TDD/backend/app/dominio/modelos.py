"""Modelos del dominio: la solicitud, la compra y el pago."""

from dataclasses import dataclass
from datetime import date
from enum import Enum


class TipoPase(str, Enum):
    """Tipo de pase: regular o VIP."""

    REGULAR = "REGULAR"
    VIP = "VIP"


class MedioPago(str, Enum):
    """Forma de pago: efectivo en boletería o tarjeta."""

    EFECTIVO = "EFECTIVO"
    TARJETA = "TARJETA"


class EstadoCompra(str, Enum):
    """Estado de la compra según su pago."""

    PENDIENTE_DE_PAGO = "PENDIENTE_DE_PAGO"
    CONFIRMADA = "CONFIRMADA"
    ANULADA = "ANULADA"


@dataclass(frozen=True)
class PagoInformado:
    """Pago tal como lo informa la pasarela (Mercado Pago)."""

    id_pago: str
    aprobado: bool
    referencia: str | None
    monto: int
    rechazado: bool = False


@dataclass(frozen=True)
class SolicitudCompra:
    """Datos que ingresa el visitante para comprar."""

    email_usuario: str
    fecha_visita: date
    cantidad: int
    edades: list[int]
    tipo_pase: TipoPase
    medio_pago: MedioPago


@dataclass
class Compra:
    """Compra registrada, con su total y el estado del pago."""

    email_usuario: str
    fecha_visita: date
    cantidad: int
    edades: list[int]
    tipo_pase: TipoPase
    medio_pago: MedioPago
    total: int
    id: int | None = None
    url_pago: str | None = None
    estado: EstadoCompra = EstadoCompra.CONFIRMADA
    referencia_pago: str | None = None

    def referencia_externa(self):
        """Devuelve la referencia del pago en Mercado Pago.

        Las compras con tarjeta anteriores a la referencia única usan su
        número, para no perder los pagos que ya estaban en curso.
        """
        return self.referencia_pago or str(self.id)

    def resumen(self):
        """Informa la cantidad de entradas compradas y la fecha."""
        palabra = "entrada" if self.cantidad == 1 else "entradas"
        return (
            f"Compraste {self.cantidad} {palabra} "
            f"para el {self.fecha_visita:%d/%m/%Y}"
        )
