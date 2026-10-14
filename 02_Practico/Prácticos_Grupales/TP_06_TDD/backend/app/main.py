from fastapi import FastAPI

app = FastAPI(title="Sistema de compra de entradas")


@app.get("/")
def inicio():
    return {"mensaje": "Sistema de compra de entradas"}