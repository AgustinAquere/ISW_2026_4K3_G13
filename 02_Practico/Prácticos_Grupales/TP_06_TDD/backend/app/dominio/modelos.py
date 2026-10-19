from dataclasses import dataclass
from datetime import date
from enum import Enum


class TipoPase(str, Enum):
    REGULAR = "REGULAR"
    VIP = "VIP"


class MedioPago(str, Enum):
    EFECTIVO = "EFECTIVO"
    TARJETA = "TARJETA"


class EstadoCompra(str, Enum):
    PENDIENTE_DE_PAGO = "PENDIENTE_DE_PAGO"
    CONFIRMADA = "CONFIRMADA"
    ANULADA = "ANULADA"


@dataclass(frozen=True)
class PagoInformado:
    """Pago tal como lo informa la pasarela (Mercado Pago)."""

    id_pago: str
    aprobado: bool
    id_compra: int | None
    monto: int
    rechazado: bool = False


@dataclass(frozen=True)
class SolicitudCompra:
    email_usuario: str
    fecha_visita: date
    cantidad: int
    edades: list[int]
    tipo_pase: TipoPase
    medio_pago: MedioPago


@dataclass
class Compra:
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

    def resumen(self):
        palabra = "entrada" if self.cantidad == 1 else "entradas"
        return (
            f"Compraste {self.cantidad} {palabra} "
            f"para el {self.fecha_visita:%d/%m/%Y}"
        )
