from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_inicio():
    respuesta = client.get("/")

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "mensaje": "Sistema de compra de entradas"
    }