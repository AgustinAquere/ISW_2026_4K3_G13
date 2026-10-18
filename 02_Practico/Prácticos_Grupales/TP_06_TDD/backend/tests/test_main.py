from app.dependencias import obtener_servicio_compra
from app.servicios.compra_service import ServicioCompra


def test_la_aplicacion_usa_un_unico_servicio_de_compra():
    servicio = obtener_servicio_compra()

    assert isinstance(servicio, ServicioCompra)
    assert obtener_servicio_compra() is servicio
