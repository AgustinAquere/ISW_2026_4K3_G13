class UsuarioNoRegistradoError(Exception):
    """El usuario que intenta comprar no está registrado."""


class CompraInvalidaError(Exception):
    """La solicitud de compra no cumple una regla de negocio."""
