import pytest
from fastapi.testclient import TestClient

from app.adaptadores.notificador import NotificadorEnMemoria
from app.adaptadores.pasarela_pago import PasarelaMercadoPagoSimulada
from app.adaptadores.repositorios import (
    RepositorioComprasEnMemoria,
    RepositorioUsuariosEnMemoria,
)
from app.dependencias import obtener_reloj, obtener_servicio_compra
from app.main import app
from app.servicios.compra_service import ServicioCompra
from tests.fechas import AHORA

EMAIL_REGISTRADO = "visitante@ecoharmony.com"


class MercadoPagoQueInforma:
    """Doble de Mercado Pago: informa el pago que indica cada prueba."""

    def __init__(self):
        self.pago = None
        self.consultados = []

    def crear_pago(self, compra):
        return f"https://www.mercadopago.com.ar/checkout?ref={compra.id}"

    def consultar_pago(self, id_pago):
        self.consultados.append(id_pago)
        return self.pago


class RelojFijo:
    """Reloj controlable para que las pruebas no dependan de la fecha real."""

    def __init__(self, ahora):
        self.ahora_actual = ahora

    def ahora(self):
        return self.ahora_actual


@pytest.fixture
def reloj():
    return RelojFijo(AHORA)


@pytest.fixture
def usuarios():
    return RepositorioUsuariosEnMemoria([EMAIL_REGISTRADO])


@pytest.fixture
def compras():
    return RepositorioComprasEnMemoria()


@pytest.fixture
def notificador():
    return NotificadorEnMemoria()


@pytest.fixture
def pasarela_pago():
    return PasarelaMercadoPagoSimulada()


@pytest.fixture
def mercado_pago():
    return MercadoPagoQueInforma()


@pytest.fixture
def servicio(reloj, usuarios, compras, notificador, pasarela_pago):
    return ServicioCompra(reloj, usuarios, compras, notificador, pasarela_pago)


@pytest.fixture
def client(servicio, reloj):
    app.dependency_overrides[obtener_servicio_compra] = lambda: servicio
    app.dependency_overrides[obtener_reloj] = lambda: reloj
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def cabecera_usuario():
    return {"X-Usuario-Email": EMAIL_REGISTRADO}
