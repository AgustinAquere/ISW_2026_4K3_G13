from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.mercado_pago_simulado import router as mercado_pago_simulado
from app.routers import compras

RUTA_FRONT = Path(__file__).resolve().parent / "static"

app = FastAPI(title="Sistema de compra de entradas")
app.include_router(compras.router)
app.include_router(mercado_pago_simulado.router)
# Se monta al final para que las rutas de la API tengan prioridad.
app.mount("/", StaticFiles(directory=RUTA_FRONT, html=True), name="front")
