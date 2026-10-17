from fastapi.testclient import TestClient

from app.dependencias import obtener_servicio_compra
from app.main import app
from app.servicios.compra_service import ServicioCompra

client = TestClient(app)


def test_inicio():
    respuesta = client.get("/")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"mensaje": "Sistema de compra de entradas"}


def test_la_aplicacion_usa_un_unico_servicio_de_compra():
    servicio = obtener_servicio_compra()

    assert isinstance(servicio, ServicioCompra)
    assert obtener_servicio_compra() is servicio
