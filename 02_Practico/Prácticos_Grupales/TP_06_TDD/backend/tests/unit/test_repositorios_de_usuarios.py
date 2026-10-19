import sqlite3

import pytest

from app.adaptadores.repositorios import RepositorioUsuariosEnMemoria
from app.adaptadores.repositorios_sqlite import RepositorioUsuariosSQLite

# Los dos repositorios de usuarios cumplen el mismo contrato.


@pytest.fixture(params=["memoria", "sqlite"])
def usuarios(request):
    if request.param == "memoria":
        yield RepositorioUsuariosEnMemoria(["existente@mail.com"])
        return
    conexion = sqlite3.connect(":memory:")
    yield RepositorioUsuariosSQLite(conexion, ["existente@mail.com"])
    conexion.close()


def test_registrar_un_email_nuevo_lo_deja_registrado(usuarios):
    assert usuarios.registrar("nuevo@mail.com") is True
    assert usuarios.esta_registrado("nuevo@mail.com")


def test_registrar_un_email_existente_no_lo_duplica(usuarios):
    assert usuarios.registrar("existente@mail.com") is False
    assert usuarios.esta_registrado("existente@mail.com")
