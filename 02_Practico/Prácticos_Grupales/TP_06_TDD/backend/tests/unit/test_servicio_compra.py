from datetime import date

import pytest

from app.adaptadores.repositorios import RepositorioUsuariosEnMemoria
from app.dominio.errores import CompraInvalidaError, UsuarioNoRegistradoError
from app.dominio.modelos import MedioPago, SolicitudCompra, TipoPase
from app.dominio.precios import PRECIO_BASE
from app.servicios.compra_service import ServicioCompra
from tests.conftest import EMAIL_REGISTRADO


def solicitud(**cambios):
    """Arma una solicitud válida; cada prueba cambia solo lo que evalúa."""
    datos = {
        "email_usuario": EMAIL_REGISTRADO,
        "fecha_visita": date(2026, 11, 15),
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


# FAQ 27 del PO: el máximo de 10 entradas es por usuario y fecha, sumando
# todas sus compras.


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
    martes = date(2026, 11, 17)

    compra = servicio.comprar(
        solicitud(cantidad=6, edades=[30] * 6, fecha_visita=martes)
    )

    assert compra.fecha_visita == martes


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


def test_compra_para_un_dia_cerrado_es_rechazada(servicio):
    lunes = date(2026, 11, 16)

    with pytest.raises(CompraInvalidaError, match="cerrado"):
        servicio.comprar(solicitud(fecha_visita=lunes))


# 4. Validación de la edad y descuentos


def test_cp18_edad_negativa_es_rechazada(servicio):
    with pytest.raises(CompraInvalidaError, match="edad"):
        servicio.comprar(solicitud(edades=[25, -1]))


def test_total_de_la_compra_suma_el_precio_de_cada_visitante(servicio):
    # Adulto (precio completo) + niño de 10 (50 %) + bebé de 2 (gratis).
    compra = servicio.comprar(
        solicitud(cantidad=3, edades=[30, 10, 2], tipo_pase=TipoPase.REGULAR)
    )

    assert compra.total == PRECIO_BASE[TipoPase.REGULAR] * 1.5


# 5. Modalidades de pago


def test_cp23_pago_en_boleteria_procesa_la_compra_sin_redirigir(
    servicio, pasarela_pago
):
    compra = servicio.comprar(solicitud(medio_pago=MedioPago.EFECTIVO))

    assert compra.url_pago is None
    assert pasarela_pago.pagos_creados == []


def test_cp24_pago_con_tarjeta_redirige_a_mercado_pago(
    servicio, pasarela_pago
):
    compra = servicio.comprar(solicitud(medio_pago=MedioPago.TARJETA))

    assert compra.url_pago.startswith("https://www.mercadopago.com.ar/")
    assert pasarela_pago.pagos_creados == [compra]


def test_compra_con_tarjeta_sin_costo_no_redirige_a_mercado_pago(
    servicio, pasarela_pago
):
    # Mercado Pago no acepta cobros de $0: los menores de 4 años no pagan.
    compra = servicio.comprar(
        solicitud(edades=[1, 3], medio_pago=MedioPago.TARJETA)
    )

    assert compra.total == 0
    assert compra.url_pago is None
    assert pasarela_pago.pagos_creados == []


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
    compra = servicio.comprar(
        solicitud(cantidad=2, fecha_visita=date(2026, 11, 15))
    )

    assert compra.resumen() == "Compraste 2 entradas para el 15/11/2026"


def test_cp26_resumen_en_singular_para_una_entrada(servicio):
    compra = servicio.comprar(solicitud(cantidad=1, edades=[30]))

    assert compra.resumen() == "Compraste 1 entrada para el 15/11/2026"
