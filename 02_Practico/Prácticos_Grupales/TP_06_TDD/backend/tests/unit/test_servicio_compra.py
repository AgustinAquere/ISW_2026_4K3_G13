import threading
import time

import pytest

from app.adaptadores.repositorios import RepositorioUsuariosEnMemoria
from app.dominio.errores import (
    CompraInvalidaError,
    CompraNoEncontradaError,
    PagoNoDisponibleError,
    UsuarioNoRegistradoError,
)
from app.dominio.modelos import (
    Compra,
    EstadoCompra,
    MedioPago,
    PagoInformado,
    SolicitudCompra,
    TipoPase,
)
from app.dominio.precios import PRECIO_BASE
from app.servicios.compra_service import ServicioCompra
from tests.conftest import EMAIL_REGISTRADO, MercadoPagoQueInforma
from tests.fechas import (
    FECHA_VISITA,
    LUNES_PROXIMO,
    OTRA_FECHA_VISITA,
    dd_mm_aaaa,
)


def solicitud(**cambios):
    """Solicitud válida; cada prueba cambia solo lo que evalúa."""
    datos = {
        "email_usuario": EMAIL_REGISTRADO,
        "fecha_visita": FECHA_VISITA,
        "cantidad": 2,
        "edades": [25, 30],
        "tipo_pase": TipoPase.REGULAR,
        "medio_pago": MedioPago.EFECTIVO,
    }
    datos.update(cambios)
    return SolicitudCompra(**datos)


def test_cp07_usuario_no_registrado_no_puede_comprar(servicio):
    with pytest.raises(UsuarioNoRegistradoError):
        servicio.comprar(solicitud(email_usuario="desconocido@mail.com"))


# 2. Validación de la cantidad de entradas


@pytest.mark.parametrize(
    "cantidad", [0, -1, 11], ids=["CP-08", "CP-09", "CP-10"]
)
def test_cantidad_fuera_de_rango_es_rechazada(servicio, cantidad):
    with pytest.raises(CompraInvalidaError, match="cantidad"):
        servicio.comprar(
            solicitud(cantidad=cantidad, edades=[30] * max(cantidad, 0))
        )


@pytest.mark.parametrize("cantidad", [1, 10], ids=["CP-11-min", "CP-11-max"])
def test_cp11_cantidad_entre_1_y_10_es_aceptada(servicio, cantidad):
    compra = servicio.comprar(
        solicitud(cantidad=cantidad, edades=[30] * cantidad)
    )

    assert compra.cantidad == cantidad


def test_cp27_cantidad_distinta_a_edades_informadas_es_rechazada(servicio):
    with pytest.raises(CompraInvalidaError, match="edad"):
        servicio.comprar(solicitud(cantidad=3, edades=[25, 30]))


# FAQ 27 del PO: el máximo de 10 entradas es por usuario y fecha,
# sumando todas sus compras.


def test_cp28_superar_10_entradas_para_una_fecha_sumando_compras_es_rechazado(
    servicio, compras
):
    servicio.comprar(solicitud(cantidad=6, edades=[30] * 6))

    with pytest.raises(CompraInvalidaError, match="misma fecha"):
        servicio.comprar(solicitud(cantidad=5, edades=[30] * 5))

    assert len(compras.listar()) == 1


def test_cp28_completar_10_entradas_para_una_fecha_es_aceptado(servicio):
    servicio.comprar(solicitud(cantidad=6, edades=[30] * 6))

    compra = servicio.comprar(solicitud(cantidad=4, edades=[30] * 4))

    assert compra.cantidad == 4


def test_cp28_el_limite_se_cuenta_por_fecha(servicio):
    servicio.comprar(solicitud(cantidad=6, edades=[30] * 6))

    compra = servicio.comprar(
        solicitud(cantidad=6, edades=[30] * 6, fecha_visita=OTRA_FECHA_VISITA)
    )

    assert compra.fecha_visita == OTRA_FECHA_VISITA


def test_cp28_el_limite_se_cuenta_por_usuario(
    reloj, compras, notificador, pasarela_pago
):
    otro_usuario = "otro@ecoharmony.com"
    servicio = ServicioCompra(
        reloj,
        RepositorioUsuariosEnMemoria([EMAIL_REGISTRADO, otro_usuario]),
        compras,
        notificador,
        pasarela_pago,
    )
    servicio.comprar(solicitud(cantidad=6, edades=[30] * 6))

    compra = servicio.comprar(
        solicitud(cantidad=6, edades=[30] * 6, email_usuario=otro_usuario)
    )

    assert compra.email_usuario == otro_usuario


def test_cp28_una_compra_pendiente_de_pago_cuenta_para_el_limite(servicio):
    # Las entradas con el pago en curso quedan reservadas: solo las
    # compras anuladas dejan de contar (DECISIONES_DE_DISENO.md,
    # FAQ 27).
    servicio.comprar(
        solicitud(cantidad=6, edades=[30] * 6, medio_pago=MedioPago.TARJETA)
    )

    with pytest.raises(CompraInvalidaError, match="misma fecha"):
        servicio.comprar(solicitud(cantidad=5, edades=[30] * 5))


def test_compra_para_un_dia_cerrado_es_rechazada(servicio):
    with pytest.raises(CompraInvalidaError, match="cerrado"):
        servicio.comprar(solicitud(fecha_visita=LUNES_PROXIMO))


# 4. Validación de la edad y descuentos


def test_cp18_edad_negativa_es_rechazada(servicio):
    with pytest.raises(CompraInvalidaError, match="edad"):
        servicio.comprar(solicitud(edades=[25, -1]))


def test_cp18_edad_0_es_aceptada(servicio):
    # Valor límite de CP-18: un bebé de meses se informa con edad 0.
    compra = servicio.comprar(solicitud(edades=[25, 0]))

    assert compra.edades == [25, 0]


def test_total_de_la_compra_suma_el_precio_de_cada_visitante(servicio):
    # Adulto (precio completo) + niño de 10 (50 %) + bebé de 2 (gratis).
    compra = servicio.comprar(
        solicitud(cantidad=3, edades=[30, 10, 2], tipo_pase=TipoPase.REGULAR)
    )

    assert compra.total == PRECIO_BASE[TipoPase.REGULAR] * 1.5


def test_total_con_pase_vip_aplica_los_descuentos_por_edad(servicio):
    # Adulto (completo) + niño de 10 (50 %) + bebé de 2 (gratis)
    # + jubilado de 65 (50 %).
    compra = servicio.comprar(
        solicitud(cantidad=4, edades=[30, 10, 2, 65], tipo_pase=TipoPase.VIP)
    )

    assert compra.total == PRECIO_BASE[TipoPase.VIP] * 2


# 5. Modalidades de pago


def test_cp23_pago_en_boleteria_procesa_la_compra_sin_redirigir(
    servicio, mercado_pago_simulado
):
    compra = servicio.comprar(solicitud(medio_pago=MedioPago.EFECTIVO))

    assert compra.url_pago is None
    assert mercado_pago_simulado.preferencias_creadas() == []


def test_cp24_pago_con_tarjeta_redirige_a_mercado_pago(
    servicio, mercado_pago_simulado
):
    compra = servicio.comprar(solicitud(medio_pago=MedioPago.TARJETA))

    (preferencia,) = mercado_pago_simulado.preferencias_creadas()
    assert compra.url_pago == preferencia["init_point"]
    assert preferencia["external_reference"] == compra.referencia_externa()


def test_compra_con_tarjeta_sin_costo_no_redirige_a_mercado_pago(
    servicio, mercado_pago_simulado
):
    # Mercado Pago no acepta cobros de $0: los menores de 4 años no
    # pagan.
    compra = servicio.comprar(
        solicitud(edades=[1, 3], medio_pago=MedioPago.TARJETA)
    )

    assert compra.total == 0
    assert compra.url_pago is None
    assert mercado_pago_simulado.preferencias_creadas() == []


def test_cp29_compra_con_tarjeta_queda_pendiente_de_pago_sin_mail(
    servicio, notificador
):
    compra = servicio.comprar(solicitud(medio_pago=MedioPago.TARJETA))

    assert compra.estado == EstadoCompra.PENDIENTE_DE_PAGO
    assert notificador.enviados == []


def test_compra_en_boleteria_queda_confirmada(servicio):
    compra = servicio.comprar(solicitud(medio_pago=MedioPago.EFECTIVO))

    assert compra.estado == EstadoCompra.CONFIRMADA


def test_compra_con_tarjeta_sin_costo_queda_confirmada_y_envia_mail(
    servicio, notificador
):
    compra = servicio.comprar(
        solicitud(edades=[1, 3], medio_pago=MedioPago.TARJETA)
    )

    assert compra.estado == EstadoCompra.CONFIRMADA
    assert notificador.enviados == [compra]


# 6. Confirmación de la compra


def test_compra_realizada_queda_registrada(servicio, compras):
    compra = servicio.comprar(solicitud())

    assert compra.id is not None
    assert compras.obtener(compra.id) == compra


def test_cp25_compra_exitosa_envia_mail_de_confirmacion(servicio, notificador):
    compra = servicio.comprar(solicitud())

    assert notificador.enviados == [compra]


def test_compra_rechazada_no_envia_mail_ni_se_registra(
    servicio, notificador, compras
):
    with pytest.raises(CompraInvalidaError):
        servicio.comprar(solicitud(cantidad=11, edades=[30] * 11))

    assert notificador.enviados == []
    assert compras.listar() == []


def test_cp26_resumen_informa_cantidad_de_entradas_y_fecha(servicio):
    compra = servicio.comprar(solicitud(cantidad=2, fecha_visita=FECHA_VISITA))

    assert compra.resumen() == (
        f"Compraste 2 entradas para el {dd_mm_aaaa(FECHA_VISITA)}"
    )


def test_cp26_resumen_en_singular_para_una_entrada(servicio):
    compra = servicio.comprar(solicitud(cantidad=1, edades=[30]))

    assert compra.resumen() == (
        f"Compraste 1 entrada para el {dd_mm_aaaa(FECHA_VISITA)}"
    )


# 7. Confirmación del pago con Mercado Pago: al volver del checkout se
# consulta el pago y, si está aprobado, se confirma la compra y se envía
# el mail.


@pytest.fixture
def servicio_mp(reloj, usuarios, compras, notificador, mercado_pago):
    return ServicioCompra(reloj, usuarios, compras, notificador, mercado_pago)


def compra_con_tarjeta(servicio_mp):
    return servicio_mp.comprar(solicitud(medio_pago=MedioPago.TARJETA))


def test_cp30_pago_aprobado_confirma_la_compra_y_envia_el_mail(
    servicio_mp, mercado_pago, compras, notificador
):
    compra = compra_con_tarjeta(servicio_mp)
    mercado_pago.pago = PagoInformado(
        "pago-1", True, compra.referencia_externa(), compra.total
    )

    confirmada = servicio_mp.confirmar_pago(
        EMAIL_REGISTRADO, compra.id, "pago-1"
    )

    assert confirmada.estado == EstadoCompra.CONFIRMADA
    assert compras.obtener(compra.id).estado == EstadoCompra.CONFIRMADA
    assert notificador.enviados == [confirmada]
    assert mercado_pago.consultados == ["pago-1"]


def test_cp31_pago_no_aprobado_deja_la_compra_pendiente_sin_mail(
    servicio_mp, mercado_pago, notificador
):
    compra = compra_con_tarjeta(servicio_mp)
    mercado_pago.pago = PagoInformado(
        "pago-1", False, compra.referencia_externa(), compra.total
    )

    resultado = servicio_mp.confirmar_pago(
        EMAIL_REGISTRADO, compra.id, "pago-1"
    )

    assert resultado.estado == EstadoCompra.PENDIENTE_DE_PAGO
    assert notificador.enviados == []


@pytest.mark.parametrize(
    "otra_compra, otro_monto",
    [(True, False), (False, True)],
    ids=["CP-32-otra-compra", "CP-32-otro-monto"],
)
def test_cp32_pago_que_no_corresponde_a_la_compra_es_rechazado(
    servicio_mp, mercado_pago, notificador, otra_compra, otro_monto
):
    compra = compra_con_tarjeta(servicio_mp)
    mercado_pago.pago = PagoInformado(
        "pago-1",
        True,
        "otra-referencia" if otra_compra else compra.referencia_externa(),
        compra.total - 1 if otro_monto else compra.total,
    )

    with pytest.raises(CompraInvalidaError, match="no corresponde"):
        servicio_mp.confirmar_pago(EMAIL_REGISTRADO, compra.id, "pago-1")

    assert compra.estado == EstadoCompra.PENDIENTE_DE_PAGO
    assert notificador.enviados == []


def test_cp33_confirmar_dos_veces_el_mismo_pago_envia_un_solo_mail(
    servicio_mp, mercado_pago, notificador
):
    compra = compra_con_tarjeta(servicio_mp)
    mercado_pago.pago = PagoInformado(
        "pago-1", True, compra.referencia_externa(), compra.total
    )

    servicio_mp.confirmar_pago(EMAIL_REGISTRADO, compra.id, "pago-1")
    servicio_mp.confirmar_pago(EMAIL_REGISTRADO, compra.id, "pago-1")

    assert len(notificador.enviados) == 1


def test_confirmar_el_pago_de_una_compra_inexistente_es_rechazado(
    servicio_mp,
):
    with pytest.raises(CompraNoEncontradaError):
        servicio_mp.confirmar_pago(EMAIL_REGISTRADO, 99, "pago-1")


def test_confirmar_el_pago_de_una_compra_de_otro_usuario_es_rechazado(
    reloj, compras, notificador, mercado_pago
):
    otro_usuario = "otro@ecoharmony.com"
    servicio = ServicioCompra(
        reloj,
        RepositorioUsuariosEnMemoria([EMAIL_REGISTRADO, otro_usuario]),
        compras,
        notificador,
        mercado_pago,
    )
    compra = compra_con_tarjeta(servicio)
    mercado_pago.pago = PagoInformado(
        "pago-1", True, compra.referencia_externa(), compra.total
    )

    with pytest.raises(CompraNoEncontradaError):
        servicio.confirmar_pago(otro_usuario, compra.id, "pago-1")

    assert notificador.enviados == []


# 8. Mercado Pago no disponible al crear el pago


def mercado_pago_caido(compra):
    raise PagoNoDisponibleError()


def test_cp34_si_mercado_pago_no_esta_disponible_la_compra_se_anula(
    servicio, pasarela_pago, compras, notificador, monkeypatch
):
    monkeypatch.setattr(pasarela_pago, "crear_pago", mercado_pago_caido)

    with pytest.raises(PagoNoDisponibleError):
        servicio.comprar(solicitud(medio_pago=MedioPago.TARJETA))

    (compra,) = compras.listar()
    assert compra.estado == EstadoCompra.ANULADA
    assert notificador.enviados == []


def test_cp34_una_compra_anulada_no_cuenta_para_el_limite_por_fecha(
    servicio, pasarela_pago, monkeypatch
):
    with monkeypatch.context() as parche:
        parche.setattr(pasarela_pago, "crear_pago", mercado_pago_caido)
        with pytest.raises(PagoNoDisponibleError):
            servicio.comprar(
                solicitud(
                    cantidad=6, edades=[30] * 6, medio_pago=MedioPago.TARJETA
                )
            )

    compra = servicio.comprar(
        solicitud(cantidad=6, edades=[30] * 6, medio_pago=MedioPago.TARJETA)
    )

    assert compra.estado == EstadoCompra.PENDIENTE_DE_PAGO


def test_confirmar_el_pago_de_una_compra_anulada_es_rechazado(
    servicio_mp, mercado_pago, compras
):
    compra = compra_con_tarjeta(servicio_mp)
    compra.estado = EstadoCompra.ANULADA
    compras.actualizar_estado(compra)
    mercado_pago.pago = PagoInformado(
        "pago-1", True, compra.referencia_externa(), compra.total
    )

    with pytest.raises(CompraInvalidaError, match="anulada"):
        servicio_mp.confirmar_pago(EMAIL_REGISTRADO, compra.id, "pago-1")

    assert mercado_pago.consultados == []


# 9. Verificación del pago sin el id del pago: Mercado Pago se abre en
# otra pestaña y el sitio busca el pago por el número de compra.


def test_cp36_verificar_un_pago_aprobado_confirma_la_compra_y_envia_el_mail(
    servicio_mp, mercado_pago, compras, notificador
):
    compra = compra_con_tarjeta(servicio_mp)
    mercado_pago.pago = PagoInformado(
        "pago-1", True, compra.referencia_externa(), compra.total
    )

    verificada, pago = servicio_mp.verificar_pago(EMAIL_REGISTRADO, compra.id)

    assert verificada.estado == EstadoCompra.CONFIRMADA
    assert compras.obtener(compra.id).estado == EstadoCompra.CONFIRMADA
    assert pago == mercado_pago.pago
    assert notificador.enviados == [verificada]
    assert mercado_pago.buscados == [compra.referencia_externa()]


def test_verificar_sin_pagos_deja_la_compra_pendiente(
    servicio_mp, mercado_pago, notificador
):
    compra = compra_con_tarjeta(servicio_mp)

    verificada, pago = servicio_mp.verificar_pago(EMAIL_REGISTRADO, compra.id)

    assert verificada.estado == EstadoCompra.PENDIENTE_DE_PAGO
    assert pago is None
    assert notificador.enviados == []


def test_verificar_un_pago_rechazado_lo_informa_y_la_compra_sigue_pendiente(
    servicio_mp, mercado_pago, notificador
):
    compra = compra_con_tarjeta(servicio_mp)
    mercado_pago.pago = PagoInformado(
        "pago-1",
        False,
        compra.referencia_externa(),
        compra.total,
        rechazado=True,
    )

    verificada, pago = servicio_mp.verificar_pago(EMAIL_REGISTRADO, compra.id)

    assert verificada.estado == EstadoCompra.PENDIENTE_DE_PAGO
    assert pago.rechazado
    assert notificador.enviados == []


def test_verificar_un_pago_por_otro_monto_es_rechazado(
    servicio_mp, mercado_pago, notificador
):
    compra = compra_con_tarjeta(servicio_mp)
    mercado_pago.pago = PagoInformado(
        "pago-1", True, compra.referencia_externa(), compra.total - 1
    )

    with pytest.raises(CompraInvalidaError, match="no corresponde"):
        servicio_mp.verificar_pago(EMAIL_REGISTRADO, compra.id)

    assert notificador.enviados == []


def test_verificar_una_compra_ya_confirmada_no_busca_ni_reenvia_el_mail(
    servicio_mp, mercado_pago, notificador
):
    compra = compra_con_tarjeta(servicio_mp)
    mercado_pago.pago = PagoInformado(
        "pago-1", True, compra.referencia_externa(), compra.total
    )
    servicio_mp.verificar_pago(EMAIL_REGISTRADO, compra.id)

    verificada, _ = servicio_mp.verificar_pago(EMAIL_REGISTRADO, compra.id)

    assert verificada.estado == EstadoCompra.CONFIRMADA
    assert mercado_pago.buscados == [compra.referencia_externa()]
    assert len(notificador.enviados) == 1


def test_verificar_el_pago_de_una_compra_de_otro_usuario_es_rechazado(
    reloj, compras, notificador, mercado_pago
):
    otro_usuario = "otro@ecoharmony.com"
    servicio = ServicioCompra(
        reloj,
        RepositorioUsuariosEnMemoria([EMAIL_REGISTRADO, otro_usuario]),
        compras,
        notificador,
        mercado_pago,
    )
    compra = compra_con_tarjeta(servicio)

    with pytest.raises(CompraNoEncontradaError):
        servicio.verificar_pago(otro_usuario, compra.id)

    assert mercado_pago.buscados == []


def test_verificar_el_pago_de_una_compra_anulada_es_rechazado(
    servicio_mp, mercado_pago, compras
):
    compra = compra_con_tarjeta(servicio_mp)
    compra.estado = EstadoCompra.ANULADA
    compras.actualizar_estado(compra)

    with pytest.raises(CompraInvalidaError, match="anulada"):
        servicio_mp.verificar_pago(EMAIL_REGISTRADO, compra.id)

    assert mercado_pago.buscados == []


# 10. Referencia de pago única: el número de compra se repite si se
# borra la base o si otro integrante usa las mismas credenciales de
# Mercado Pago, así que la búsqueda de pagos no puede usarlo.


def test_cp37_cada_compra_con_tarjeta_tiene_una_referencia_de_pago_unica(
    servicio_mp,
):
    primera = compra_con_tarjeta(servicio_mp)
    segunda = compra_con_tarjeta(servicio_mp)

    assert primera.referencia_pago
    assert primera.referencia_pago != segunda.referencia_pago
    assert primera.referencia_pago != str(primera.id)
    assert primera.referencia_externa() == primera.referencia_pago


def test_cp37_un_pago_de_otra_compra_con_el_mismo_numero_no_la_confirma(
    servicio_mp, mercado_pago, notificador
):
    # Por ejemplo, el pago de la compra 1 de una base anterior.
    compra = compra_con_tarjeta(servicio_mp)
    mercado_pago.pago = PagoInformado(
        "pago-ajeno", True, str(compra.id), compra.total
    )

    with pytest.raises(CompraInvalidaError, match="no corresponde"):
        servicio_mp.verificar_pago(EMAIL_REGISTRADO, compra.id)

    assert compra.estado == EstadoCompra.PENDIENTE_DE_PAGO
    assert notificador.enviados == []


def test_una_compra_sin_referencia_de_pago_usa_su_numero():
    # Compras con tarjeta registradas antes de la referencia única.
    compra = Compra(
        email_usuario=EMAIL_REGISTRADO,
        fecha_visita=FECHA_VISITA,
        cantidad=1,
        edades=[30],
        tipo_pase=TipoPase.REGULAR,
        medio_pago=MedioPago.TARJETA,
        total=10000,
        id=7,
    )

    assert compra.referencia_externa() == "7"


# 11. Verificaciones simultáneas: al volver a la pestaña del sitio
# pueden llegar dos consultas a la vez (la del intervalo y la de
# visibilitychange), y FastAPI las atiende en hilos distintos.


class MercadoPagoLento(MercadoPagoQueInforma):
    """Tarda en responder, como la API real: las consultas se pisan."""

    def buscar_pago(self, referencia):
        time.sleep(0.2)
        return super().buscar_pago(referencia)


def test_dos_verificaciones_al_mismo_tiempo_envian_un_solo_mail(
    reloj, usuarios, compras, notificador
):
    mercado_pago = MercadoPagoLento()
    servicio = ServicioCompra(
        reloj, usuarios, compras, notificador, mercado_pago
    )
    compra = compra_con_tarjeta(servicio)
    mercado_pago.pago = PagoInformado(
        "pago-1", True, compra.referencia_externa(), compra.total
    )
    hilos = [
        threading.Thread(
            target=servicio.verificar_pago, args=(EMAIL_REGISTRADO, compra.id)
        )
        for _ in range(2)
    ]

    for hilo in hilos:
        hilo.start()
    for hilo in hilos:
        hilo.join()

    assert compra.estado == EstadoCompra.CONFIRMADA
    assert len(notificador.enviados) == 1


# 12. Cancelar una compra pendiente de pago: la compra se registra
# antes de pagar, así que cancelarla la anula y libera sus entradas.


def test_cp40_cancelar_una_compra_pendiente_la_anula(
    servicio_mp, compras, notificador
):
    compra = compra_con_tarjeta(servicio_mp)

    anulada = servicio_mp.anular_compra(EMAIL_REGISTRADO, compra.id)

    assert anulada.estado == EstadoCompra.ANULADA
    assert compras.obtener(compra.id).estado == EstadoCompra.ANULADA
    assert notificador.enviados == []


def test_cp40_una_compra_cancelada_no_cuenta_para_el_limite(servicio_mp):
    compra = servicio_mp.comprar(
        solicitud(cantidad=1, edades=[30], medio_pago=MedioPago.TARJETA)
    )

    servicio_mp.anular_compra(EMAIL_REGISTRADO, compra.id)
    completa = servicio_mp.comprar(solicitud(cantidad=10, edades=[30] * 10))

    assert completa.cantidad == 10


def test_cancelar_una_compra_inexistente_es_rechazado(servicio_mp):
    with pytest.raises(CompraNoEncontradaError):
        servicio_mp.anular_compra(EMAIL_REGISTRADO, 99)


def test_cancelar_una_compra_de_otro_usuario_es_rechazado(
    reloj, compras, notificador, mercado_pago
):
    otro_usuario = "otro@ecoharmony.com"
    servicio = ServicioCompra(
        reloj,
        RepositorioUsuariosEnMemoria([EMAIL_REGISTRADO, otro_usuario]),
        compras,
        notificador,
        mercado_pago,
    )
    compra = compra_con_tarjeta(servicio)

    with pytest.raises(CompraNoEncontradaError):
        servicio.anular_compra(otro_usuario, compra.id)

    assert compras.obtener(compra.id).estado == EstadoCompra.PENDIENTE_DE_PAGO


def test_una_compra_confirmada_no_se_puede_cancelar(servicio_mp, compras):
    compra = servicio_mp.comprar(solicitud(medio_pago=MedioPago.EFECTIVO))

    with pytest.raises(CompraInvalidaError, match="confirmada"):
        servicio_mp.anular_compra(EMAIL_REGISTRADO, compra.id)

    assert compras.obtener(compra.id).estado == EstadoCompra.CONFIRMADA


def test_cancelar_dos_veces_la_misma_compra_no_falla(servicio_mp):
    # Por ejemplo, un doble clic en "Cancelar".
    compra = compra_con_tarjeta(servicio_mp)
    servicio_mp.anular_compra(EMAIL_REGISTRADO, compra.id)

    anulada = servicio_mp.anular_compra(EMAIL_REGISTRADO, compra.id)

    assert anulada.estado == EstadoCompra.ANULADA


def test_cancelar_una_compra_ya_pagada_la_confirma_en_vez_de_anularla(
    servicio_mp, mercado_pago, compras, notificador
):
    # El usuario pagó en la pestaña de Mercado Pago y tocó "Cancelar"
    # antes de que el sitio detectara el pago.
    compra = compra_con_tarjeta(servicio_mp)
    mercado_pago.pago = PagoInformado(
        "pago-1", True, compra.referencia_externa(), compra.total
    )

    resultado = servicio_mp.anular_compra(EMAIL_REGISTRADO, compra.id)

    assert resultado.estado == EstadoCompra.CONFIRMADA
    assert compras.obtener(compra.id).estado == EstadoCompra.CONFIRMADA
    assert notificador.enviados == [resultado]


def test_si_mercado_pago_no_responde_la_compra_no_se_cancela(
    servicio_mp, mercado_pago, compras, monkeypatch
):
    compra = compra_con_tarjeta(servicio_mp)
    monkeypatch.setattr(mercado_pago, "buscar_pago", mercado_pago_caido)

    with pytest.raises(PagoNoDisponibleError):
        servicio_mp.anular_compra(EMAIL_REGISTRADO, compra.id)

    assert compras.obtener(compra.id).estado == EstadoCompra.PENDIENTE_DE_PAGO


def test_cancelar_mientras_se_verifica_el_pago_envia_un_solo_mail(
    reloj, usuarios, compras, notificador
):
    mercado_pago = MercadoPagoLento()
    servicio = ServicioCompra(
        reloj, usuarios, compras, notificador, mercado_pago
    )
    compra = compra_con_tarjeta(servicio)
    mercado_pago.pago = PagoInformado(
        "pago-1", True, compra.referencia_externa(), compra.total
    )
    hilos = [
        threading.Thread(target=accion, args=(EMAIL_REGISTRADO, compra.id))
        for accion in (servicio.verificar_pago, servicio.anular_compra)
    ]

    for hilo in hilos:
        hilo.start()
    for hilo in hilos:
        hilo.join()

    assert compra.estado == EstadoCompra.CONFIRMADA
    assert len(notificador.enviados) == 1
