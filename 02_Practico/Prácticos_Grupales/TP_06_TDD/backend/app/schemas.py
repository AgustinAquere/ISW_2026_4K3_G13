from datetime import date
from pydantic import BaseModel

class CompraRequest(BaseModel):
    fecha_visita: date
    cantidad: int
    edades: list[int]
    tipo_pase: str
    medio_pago: str


