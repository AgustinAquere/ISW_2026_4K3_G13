class UsuarioNoRegistradoError(Exception):
    """El usuario que intenta comprar no está registrado."""


class CompraNoEncontradaError(Exception):
    """La compra no existe o pertenece a otro usuario."""


class CompraInvalidaError(Exception):
    """La solicitud de compra no cumple una regla de negocio."""


class PagoNoDisponibleError(Exception):
    """No se pudo iniciar el pago con la pasarela externa."""
