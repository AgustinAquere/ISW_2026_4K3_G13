
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_inicio():
    respuesta = client.get("/")

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "mensaje": "Sistema de compra de entradas"
    }


#Test compra de entradas y datos obligatorios


def test_comprar_sin_medio_de_pago():
    respuesta = client.post(
        "/compras",
        json={
            "fecha_visita": "2026-11-15",
            "cantidad": 2,
            "edades": [25, 30],
            "tipo_pase": "COMUN"
        }
    )

    assert respuesta.status_code == 422

def test_comprar_sin_fecha_visita():
    respuesta = client.post(
        "/compras",
        json={
            "cantidad": 2,
            "edades": [25, 30],
            "tipo_pase": "COMUN",
            "medio_pago": "EFECTIVO"
        }
    )

    assert respuesta.status_code == 422

def test_comprar_sin_cantidad_de_entradas():
    respuesta = client.post(
        "/compras",
        json={
            "fecha_visita": "2026-11-15",
            "edades": [25, 30],
            "tipo_pase": "COMUN",
            "medio_pago": "EFECTIVO"
        }
    )

    assert respuesta.status_code == 422

def test_comprar_sin_edades():
    respuesta = client.post(
        "/compras",
        json={
            "fecha_visita": "2026-11-15",
            "cantidad": 2,
            "tipo_pase": "COMUN",
            "medio_pago": "EFECTIVO"
        }
    )

    assert respuesta.status_code == 422

def test_comprar_sin_tipo_de_pase():
    respuesta = client.post(
        "/compras",
        json={
            "fecha_visita": "2026-11-15",
            "cantidad": 2,
            "edades": [25, 30],
            "medio_pago": "EFECTIVO"
        }
    )

    assert respuesta.status_code == 422

def test_comprar_sin_iniciar_sesion():
    respuesta = client.post(
        "/compras",
        json={
            "fecha_visita": "2026-11-15",
            "cantidad": 2,
            "edades": [25, 30],
            "tipo_pase": "REGULAR",
            "medio_pago": "EFECTIVO"
        }
    )

    assert respuesta.status_code == 401