import sqlite3
from datetime import date

import pytest

from app.adaptadores.repositorios_sqlite import (
    RepositorioComprasSQLite,
    RepositorioUsuariosSQLite,
)
from app.dominio.modelos import Compra, MedioPago, SolicitudCompra, TipoPase
from app.servicios.compra_service import ServicioCompra
from tests.conftest import EMAIL_REGISTRADO


@pytest.fixture
def conexion():
    conexion = sqlite3.connect(":memory:")
    yield conexion
    conexion.close()


def compra_nueva(**cambios):
    """Arma una compra válida; cada prueba cambia solo lo que evalúa."""
    datos = {
        "email_usuario": EMAIL_REGISTRADO,
        "fecha_visita": date(2026, 11, 15),
        "cantidad": 2,
        "edades": [40, 8],
        "tipo_pase": TipoPase.VIP,
        "medio_pago": MedioPago.TARJETA,
        "total": 30000,
    }
    datos.update(cambios)
    return Compra(**datos)


# Usuarios


def test_usuario_cargado_esta_registrado(conexion):
    usuarios = RepositorioUsuariosSQLite(conexion, [EMAIL_REGISTRADO])

    assert usuarios.esta_registrado(EMAIL_REGISTRADO)


def test_usuario_no_cargado_no_esta_registrado(conexion):
    usuarios = RepositorioUsuariosSQLite(conexion, [EMAIL_REGISTRADO])

    assert not usuarios.esta_registrado("desconocido@mail.com")


def test_cargar_un_usuario_ya_registrado_no_lo_duplica(conexion):
    RepositorioUsuariosSQLite(conexion, [EMAIL_REGISTRADO])
    RepositorioUsuariosSQLite(conexion, [EMAIL_REGISTRADO])

    cantidad = conexion.execute("SELECT COUNT(*) FROM usuarios").fetchone()
    assert cantidad == (1,)


# Compras


def test_guardar_asigna_ids_correlativos(conexion):
    compras = RepositorioComprasSQLite(conexion)

    primera = compras.guardar(compra_nueva())
    segunda = compras.guardar(compra_nueva())

    assert (primera.id, segunda.id) == (1, 2)


def test_obtener_devuelve_la_compra_guardada(conexion):
    compras = RepositorioComprasSQLite(conexion)
    compra = compras.guardar(compra_nueva())

    assert compras.obtener(compra.id) == compra


def test_obtener_una_compra_inexistente_devuelve_none(conexion):
    compras = RepositorioComprasSQLite(conexion)

    assert compras.obtener(99) is None


def test_listar_devuelve_todas_las_compras_en_orden(conexion):
    compras = RepositorioComprasSQLite(conexion)
    primera = compras.guardar(compra_nueva(edades=[30, 30]))
    segunda = compras.guardar(
        compra_nueva(cantidad=1, edades=[70], medio_pago=MedioPago.EFECTIVO)
    )

    assert compras.listar() == [primera, segunda]


def test_sin_compras_listar_devuelve_lista_vacia(conexion):
    assert RepositorioComprasSQLite(conexion).listar() == []


# Persistencia: el motivo de usar SQLite


def test_los_datos_persisten_al_reabrir_la_base(tmp_path):
    ruta = tmp_path / "ecoharmony.db"
    conexion = sqlite3.connect(ruta)
    RepositorioUsuariosSQLite(conexion, [EMAIL_REGISTRADO])
    compra = RepositorioComprasSQLite(conexion).guardar(compra_nueva())
    conexion.close()

    conexion = sqlite3.connect(ruta)
    try:
        assert RepositorioUsuariosSQLite(conexion).esta_registrado(
            EMAIL_REGISTRADO
        )
        assert RepositorioComprasSQLite(conexion).obtener(compra.id) == compra
    finally:
        conexion.close()


def test_servicio_registra_la_compra_en_sqlite(
    conexion, reloj, notificador, pasarela_pago
):
    compras = RepositorioComprasSQLite(conexion)
    servicio = ServicioCompra(
        reloj,
        RepositorioUsuariosSQLite(conexion, [EMAIL_REGISTRADO]),
        compras,
        notificador,
        pasarela_pago,
    )

    compra = servicio.comprar(
        SolicitudCompra(
            email_usuario=EMAIL_REGISTRADO,
            fecha_visita=date(2026, 11, 15),
            cantidad=2,
            edades=[25, 30],
            tipo_pase=TipoPase.REGULAR,
            medio_pago=MedioPago.EFECTIVO,
        )
    )

    assert compras.obtener(compra.id) == compra
