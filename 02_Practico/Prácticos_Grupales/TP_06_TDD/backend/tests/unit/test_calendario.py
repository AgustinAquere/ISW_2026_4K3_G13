from datetime import time, timedelta

import pytest

from app.dominio.calendario import fechas_disponibles, validar_fecha_visita
from app.dominio.errores import CompraInvalidaError
from tests.fechas import (
    AHORA,
    FECHA_VISITA,
    HOY,
    LUNES_PROXIMO,
    UN_DIA,
    a_las,
    abierto,
    proximo_feriado,
    siguiente_dia_abierto,
)

# Todas las fechas se calculan a partir del día en que se ejecutan las
# pruebas (ver tests/fechas.py).


# 3. Validación de la fecha de visita


def test_cp12_fecha_anterior_a_hoy_es_rechazada():
    # Ayer (valor límite). HOY se eligió para que ayer el parque abriera:
    # así solo aplica la regla de fecha pasada.
    with pytest.raises(CompraInvalidaError, match="pasada"):
        validar_fecha_visita(HOY - UN_DIA, AHORA)


def test_cp13_lunes_es_rechazado():
    with pytest.raises(CompraInvalidaError, match="cerrado"):
        validar_fecha_visita(LUNES_PROXIMO, AHORA)


@pytest.mark.parametrize(
    "mes, dia",
    [(1, 1), (12, 25)],
    ids=["CP-14-1-de-enero", "CP-15-25-de-diciembre"],
)
def test_feriado_en_que_cierra_el_parque_es_rechazado(mes, dia):
    feriado = proximo_feriado(mes, dia)
    # Unos días antes del feriado, para que esté dentro de los 31 días.
    unos_dias_antes = a_las(feriado - timedelta(days=5), time(10, 0))

    with pytest.raises(CompraInvalidaError, match="cerrado"):
        validar_fecha_visita(feriado, unos_dias_antes)


def test_cp16_fecha_a_mas_de_31_dias_es_rechazada():
    with pytest.raises(CompraInvalidaError, match="31 días"):
        validar_fecha_visita(HOY + timedelta(days=32), AHORA)


def test_cp16_fecha_a_exactamente_31_dias_es_aceptada():
    # HOY se eligió para que a 31 días el parque abra.
    validar_fecha_visita(HOY + timedelta(days=31), AHORA)


def test_cp17_comprar_para_hoy_despues_de_las_17_30_es_rechazado():
    with pytest.raises(CompraInvalidaError, match="17:30"):
        validar_fecha_visita(HOY, a_las(HOY, time(17, 31)))


def test_cp17_comprar_para_hoy_a_las_17_30_es_aceptado():
    validar_fecha_visita(HOY, a_las(HOY, time(17, 30)))


def test_fecha_futura_con_parque_abierto_es_aceptada():
    validar_fecha_visita(FECHA_VISITA, AHORA)


# Fechas que el calendario del front ofrece (FAQ 2: los días cerrados no se
# pueden elegir).


def test_fechas_disponibles_van_de_hoy_a_31_dias_sin_lunes():
    ventana = [HOY + timedelta(days=dias) for dias in range(32)]

    fechas = fechas_disponibles(AHORA)

    assert fechas == [fecha for fecha in ventana if abierto(fecha)]
    assert fechas[0] == HOY
    assert fechas[-1] == HOY + timedelta(days=31)
    assert LUNES_PROXIMO not in fechas


def test_despues_de_las_17_30_hoy_no_esta_disponible():
    fechas = fechas_disponibles(a_las(HOY, time(17, 31)))

    assert fechas[0] == siguiente_dia_abierto(HOY + UN_DIA)


def test_fechas_disponibles_excluyen_los_feriados():
    navidad = proximo_feriado(12, 25)
    anio_nuevo = navidad.replace(year=navidad.year + 1, month=1, day=1)

    fechas = fechas_disponibles(a_las(navidad - timedelta(days=10), time(10)))

    assert navidad not in fechas
    assert anio_nuevo not in fechas
    assert siguiente_dia_abierto(navidad + UN_DIA) in fechas
