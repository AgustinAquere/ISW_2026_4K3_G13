from datetime import date, datetime

import pytest

from app.dominio.calendario import validar_fecha_visita
from app.dominio.errores import CompraInvalidaError

# Martes 10/11/2026 a las 10:00.
AHORA = datetime(2026, 11, 10, 10, 0)
# Domingo 20/12/2026: cerca de los feriados y dentro de la ventana de 31 días.
AHORA_FIN_DE_ANIO = datetime(2026, 12, 20, 10, 0)


# 3. Validación de la fecha de visita


def test_cp12_fecha_anterior_a_hoy_es_rechazada():
    # Ayer (valor límite) y no lunes, para que solo aplique la regla de
    # fecha pasada: hoy miércoles 11/11, visita el martes 10/11.
    miercoles = datetime(2026, 11, 11, 10, 0)

    with pytest.raises(CompraInvalidaError, match="pasada"):
        validar_fecha_visita(date(2026, 11, 10), miercoles)


def test_cp13_lunes_es_rechazado():
    with pytest.raises(CompraInvalidaError, match="cerrado"):
        validar_fecha_visita(date(2026, 11, 16), AHORA)


@pytest.mark.parametrize(
    "feriado",
    [date(2027, 1, 1), date(2026, 12, 25)],
    ids=["CP-14-1-de-enero", "CP-15-25-de-diciembre"],
)
def test_feriado_en_que_cierra_el_parque_es_rechazado(feriado):
    with pytest.raises(CompraInvalidaError, match="cerrado"):
        validar_fecha_visita(feriado, AHORA_FIN_DE_ANIO)


def test_cp16_fecha_a_mas_de_31_dias_es_rechazada():
    with pytest.raises(CompraInvalidaError, match="31 días"):
        validar_fecha_visita(date(2026, 12, 12), AHORA)


def test_cp16_fecha_a_exactamente_31_dias_es_aceptada():
    validar_fecha_visita(date(2026, 12, 11), AHORA)


def test_cp17_comprar_para_hoy_despues_de_las_17_30_es_rechazado():
    with pytest.raises(CompraInvalidaError, match="17:30"):
        validar_fecha_visita(
            date(2026, 11, 10), datetime(2026, 11, 10, 17, 31)
        )


def test_cp17_comprar_para_hoy_a_las_17_30_es_aceptado():
    validar_fecha_visita(date(2026, 11, 10), datetime(2026, 11, 10, 17, 30))


def test_fecha_futura_con_parque_abierto_es_aceptada():
    validar_fecha_visita(date(2026, 11, 15), AHORA)
