from fastapi import APIRouter
from app.schemas import CompraRequest

router = APIRouter()


@router.post("/compras")
def comprar_entradas(compra: CompraRequest):
    return {"mensaje": "Solicitud de compra recibida"}