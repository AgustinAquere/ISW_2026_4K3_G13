from app.dominio.calendario import validar_fecha_visita
from app.dominio.errores import CompraInvalidaError, UsuarioNoRegistradoError
from app.dominio.modelos import Compra, MedioPago
from app.dominio.precios import calcular_precio_entrada

CANTIDAD_MAXIMA = 10


class ServicioCompra:
    def __init__(self, reloj, usuarios, compras, notificador, pasarela_pago):
        self._reloj = reloj
        self._usuarios = usuarios
        self._compras = compras
        self._notificador = notificador
        self._pasarela_pago = pasarela_pago

    def comprar(self, solicitud):
        self._validar(solicitud)
        compra = Compra(
            email_usuario=solicitud.email_usuario,
            fecha_visita=solicitud.fecha_visita,
            cantidad=solicitud.cantidad,
            edades=solicitud.edades,
            tipo_pase=solicitud.tipo_pase,
            medio_pago=solicitud.medio_pago,
            total=self._calcular_total(solicitud),
        )
        self._compras.guardar(compra)
        if compra.medio_pago == MedioPago.TARJETA:
            compra.url_pago = self._pasarela_pago.crear_pago(compra)
        self._notificador.enviar_confirmacion(compra)
        return compra

    def _validar(self, solicitud):
        if not self._usuarios.esta_registrado(solicitud.email_usuario):
            raise UsuarioNoRegistradoError()
        self._validar_cantidad_y_edades(solicitud)
        validar_fecha_visita(solicitud.fecha_visita, self._reloj.ahora())

    @staticmethod
    def _validar_cantidad_y_edades(solicitud):
        if not 1 <= solicitud.cantidad <= CANTIDAD_MAXIMA:
            raise CompraInvalidaError(
                "La cantidad de entradas debe estar entre 1 y "
                f"{CANTIDAD_MAXIMA}"
            )
        if len(solicitud.edades) != solicitud.cantidad:
            raise CompraInvalidaError("Debe indicar la edad de cada visitante")
        if any(edad < 0 for edad in solicitud.edades):
            raise CompraInvalidaError(
                "La edad de un visitante no puede ser negativa"
            )

    @staticmethod
    def _calcular_total(solicitud):
        return sum(
            calcular_precio_entrada(edad, solicitud.tipo_pase)
            for edad in solicitud.edades
        )
