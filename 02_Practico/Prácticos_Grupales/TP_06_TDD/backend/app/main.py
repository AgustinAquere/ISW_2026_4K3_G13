from fastapi import FastAPI

from app.routers import compras

app = FastAPI(title="Sistema de compra de entradas")


@app.get("/")
def inicio():
    return {"mensaje": "Sistema de compra de entradas"}


app.include_router(compras.router)
