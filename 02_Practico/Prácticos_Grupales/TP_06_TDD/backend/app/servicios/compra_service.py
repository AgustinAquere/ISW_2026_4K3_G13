"""Caso de uso: comprar entradas y confirmar su pago."""

import threading
import uuid

from app.dominio.calendario import validar_fecha_visita
from app.dominio.errores import (
    CompraInvalidaError,
    CompraNoEncontradaError,
    PagoNoDisponibleError,
    UsuarioNoRegistradoError,
)
from app.dominio.modelos import Compra, EstadoCompra, MedioPago
from app.dominio.precios import calcular_precio_entrada

CANTIDAD_MAXIMA = 10


class ServicioCompra:
    """Valida, calcula el total, registra, cobra y avisa por mail."""

    def __init__(self, reloj, usuarios, compras, notificador, pasarela_pago):
        """Recibe el reloj, los repositorios, el mail y la pasarela."""
        self._reloj = reloj
        self._usuarios = usuarios
        self._compras = compras
        self._notificador = notificador
        self._pasarela_pago = pasarela_pago
        # FastAPI atiende cada solicitud en un hilo: confirmar o
        # verificar un pago se hace de a uno para que el mail salga una
        # sola vez.
        self._pagos_en_curso = threading.Lock()

    def comprar(self, solicitud):
        """Registra la compra si cumple todas las reglas.

        Con tarjeta y un total mayor a $0 queda pendiente de pago y se
        genera el link de Mercado Pago; si no, se confirma y se envía el
        mail. Lanza UsuarioNoRegistradoError, CompraInvalidaError o
        PagoNoDisponibleError.
        """
        self._validar(solicitud)
        total = self._calcular_total(solicitud)
        estado = self._estado_inicial(solicitud.medio_pago, total)
        compra = Compra(
            email_usuario=solicitud.email_usuario,
            fecha_visita=solicitud.fecha_visita,
            cantidad=solicitud.cantidad,
            edades=solicitud.edades,
            tipo_pase=solicitud.tipo_pase,
            medio_pago=solicitud.medio_pago,
            total=total,
            estado=estado,
            # El número de compra se repite si se borra la base o si
            # otro integrante usa las mismas credenciales: el pago se
            # busca por una referencia única.
            referencia_pago=uuid.uuid4().hex
            if estado == EstadoCompra.PENDIENTE_DE_PAGO
            else None,
        )
        self._compras.guardar(compra)
        if compra.estado == EstadoCompra.PENDIENTE_DE_PAGO:
            self._iniciar_pago(compra)
        else:
            self._notificador.enviar_confirmacion(compra)
        return compra

    def confirmar_pago(self, email_usuario, id_compra, id_pago):
        """Confirma la compra con el pago informado al volver."""
        with self._pagos_en_curso:
            compra = self._compra_con_pago_pendiente(email_usuario, id_compra)
            if compra.estado == EstadoCompra.CONFIRMADA:
                return compra
            self._aplicar_pago(
                compra, self._pasarela_pago.consultar_pago(id_pago)
            )
            return compra

    def verificar_pago(self, email_usuario, id_compra):
        """Busca el pago de la compra (si se pagó en otra pestaña)."""
        with self._pagos_en_curso:
            compra = self._compra_con_pago_pendiente(email_usuario, id_compra)
            if compra.estado == EstadoCompra.CONFIRMADA:
                return compra, None
            pago = self._pasarela_pago.buscar_pago(compra.referencia_externa())
            if pago is not None:
                self._aplicar_pago(compra, pago)
            return compra, pago

    def anular_compra(self, email_usuario, id_compra):
        """Anula la compra pendiente que el usuario cancela."""
        compra = self._compras.obtener(id_compra)
        self._cambiar_estado(compra, EstadoCompra.ANULADA)
        return compra

    def _compra_con_pago_pendiente(self, email_usuario, id_compra):
        compra = self._compras.obtener(id_compra)
        if compra is None or compra.email_usuario != email_usuario:
            raise CompraNoEncontradaError()
        if compra.estado == EstadoCompra.ANULADA:
            raise CompraInvalidaError("La compra fue anulada")
        return compra

    def _aplicar_pago(self, compra, pago):
        if (
            pago.referencia != compra.referencia_externa()
            or pago.monto != compra.total
        ):
            raise CompraInvalidaError("El pago no corresponde a la compra")
        if pago.aprobado:
            self._cambiar_estado(compra, EstadoCompra.CONFIRMADA)
            self._notificador.enviar_confirmacion(compra)

    def _iniciar_pago(self, compra):
        try:
            compra.url_pago = self._pasarela_pago.crear_pago(compra)
        except PagoNoDisponibleError:
            # Sin link de pago la compra no se puede completar: se anula
            # para que no cuente en el límite de entradas por fecha.
            self._cambiar_estado(compra, EstadoCompra.ANULADA)
            raise

    def _cambiar_estado(self, compra, estado):
        compra.estado = estado
        self._compras.actualizar_estado(compra)

    @staticmethod
    def _estado_inicial(medio_pago, total):
        # Con tarjeta se confirma cuando Mercado Pago aprueba el pago.
        # Una compra sin costo no pasa por Mercado Pago, que no cobra
        # $0.
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
