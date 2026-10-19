import pytest

from app.dependencias import obtener_usuarios
from app.main import app
from tests.conftest import EMAIL_REGISTRADO
from tests.test_api_compras import solicitud_valida

EMAIL_NUEVO = "nuevo@mail.com"

# Registro simulado sin contraseña: el registro real pertenece a otra User
# Story (FAQ 19). Sirve para mostrar que solo un usuario registrado puede
# comprar (CP-07).


@pytest.fixture
def cliente(client, usuarios):
    """Cliente cuyo registro usa el mismo repositorio que la compra."""
    app.dependency_overrides[obtener_usuarios] = lambda: usuarios
    return client


def registrar(cliente, email):
    return cliente.post("/usuarios", json={"email": email})


def comprar(cliente, email):
    return cliente.post(
        "/compras", json=solicitud_valida(), headers={"X-Usuario-Email": email}
    )


def test_registrar_un_email_nuevo_responde_201(cliente):
    respuesta = registrar(cliente, EMAIL_NUEVO)

    assert respuesta.status_code == 201
    assert respuesta.json() == {"email": EMAIL_NUEVO}


def test_cp38_un_email_no_registrado_puede_comprar_despues_de_registrarse(
    cliente,
):
    rechazada = comprar(cliente, EMAIL_NUEVO)
    registrar(cliente, EMAIL_NUEVO)
    aceptada = comprar(cliente, EMAIL_NUEVO)

    assert rechazada.status_code == 401
    assert rechazada.json()["detail"] == "Usuario no registrado"
    assert aceptada.status_code == 201


def test_registrar_un_email_ya_registrado_responde_409(cliente):
    respuesta = registrar(cliente, EMAIL_REGISTRADO)

    assert respuesta.status_code == 409
    assert respuesta.json()["detail"] == "El email ya está registrado"


@pytest.mark.parametrize(
    "email", ["", "sin-arroba", "a@b", "con espacio@mail.com"]
)
def test_registrar_un_email_invalido_responde_422(cliente, email):
    assert registrar(cliente, email).status_code == 422


def test_el_email_se_registra_sin_espacios_y_en_minusculas(cliente):
    respuesta = registrar(cliente, "  Nuevo@Mail.COM ")

    assert respuesta.json() == {"email": EMAIL_NUEVO}
    assert comprar(cliente, EMAIL_NUEVO).status_code == 201
