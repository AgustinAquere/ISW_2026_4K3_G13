from app.dominio.calendario import validar_fecha_visita
from app.dominio.errores import (
    CompraInvalidaError,
    CompraNoEncontradaError,
    UsuarioNoRegistradoError,
)
from app.dominio.modelos import Compra, EstadoCompra, MedioPago
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
        total = self._calcular_total(solicitud)
        compra = Compra(
            email_usuario=solicitud.email_usuario,
            fecha_visita=solicitud.fecha_visita,
            cantidad=solicitud.cantidad,
            edades=solicitud.edades,
            tipo_pase=solicitud.tipo_pase,
            medio_pago=solicitud.medio_pago,
            total=total,
            estado=self._estado_inicial(solicitud.medio_pago, total),
        )
        self._compras.guardar(compra)
        if compra.estado == EstadoCompra.PENDIENTE_DE_PAGO:
            compra.url_pago = self._pasarela_pago.crear_pago(compra)
        else:
            self._notificador.enviar_confirmacion(compra)
        return compra

    def confirmar_pago(self, email_usuario, id_compra, id_pago):
        compra = self._compras.obtener(id_compra)
        if compra is None or compra.email_usuario != email_usuario:
            raise CompraNoEncontradaError()
        if compra.estado == EstadoCompra.CONFIRMADA:
            return compra
        pago = self._pasarela_pago.consultar_pago(id_pago)
        if pago.id_compra != compra.id or pago.monto != compra.total:
            raise CompraInvalidaError("El pago no corresponde a la compra")
        if pago.aprobado:
            compra.estado = EstadoCompra.CONFIRMADA
            self._compras.actualizar_estado(compra)
            self._notificador.enviar_confirmacion(compra)
        return compra

    @staticmethod
    def _estado_inicial(medio_pago, total):
        # Con tarjeta se confirma cuando Mercado Pago aprueba el pago. Una
        # compra sin costo no pasa por Mercado Pago, que no cobra $0.
        if medio_pago == MedioPago.TARJETA and total > 0:
            return EstadoCompra.PENDIENTE_DE_PAGO
        return EstadoCompra.CONFIRMADA

    def _validar(self, solicitud):
        if not self._usuarios.esta_registrado(solicitud.email_usuario):
            raise UsuarioNoRegistradoError()
        self._validar_cantidad_y_edades(solicitud)
        validar_fecha_visita(solicitud.fecha_visita, self._reloj.ahora())
        self._validar_limite_por_fecha(solicitud)

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

    def _validar_limite_por_fecha(self, solicitud):
        ya_compradas = self._compras.entradas_compradas(
            solicitud.email_usuario, solicitud.fecha_visita
        )
        if ya_compradas + solicitud.cantidad > CANTIDAD_MAXIMA:
            raise CompraInvalidaError(
                f"No se pueden comprar más de {CANTIDAD_MAXIMA} entradas "
                f"para la misma fecha (ya compraste {ya_compradas})"
            )

    @staticmethod
    def _calcular_total(solicitud):
        return sum(
            calcular_precio_entrada(edad, solicitud.tipo_pase)
            for edad in solicitud.edades
        )
