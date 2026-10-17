import pytest

from app.dominio.modelos import TipoPase
from app.dominio.precios import PRECIO_BASE, calcular_precio_entrada

REGULAR = PRECIO_BASE[TipoPase.REGULAR]


# 4. Validación de la edad y descuentos


@pytest.mark.parametrize("edad", [0, 3], ids=["CP-19-0", "CP-19-3"])
def test_cp19_hasta_3_anios_no_tiene_costo(edad):
    assert calcular_precio_entrada(edad, TipoPase.REGULAR) == 0


@pytest.mark.parametrize("edad", [4, 15], ids=["CP-20-4", "CP-20-15"])
def test_cp20_de_4_a_15_anios_tiene_50_por_ciento_de_descuento(edad):
    assert calcular_precio_entrada(edad, TipoPase.REGULAR) == REGULAR / 2


@pytest.mark.parametrize("edad", [16, 59], ids=["CP-21-16", "CP-21-59"])
def test_cp21_de_16_a_59_anios_paga_precio_completo(edad):
    assert calcular_precio_entrada(edad, TipoPase.REGULAR) == REGULAR


@pytest.mark.parametrize("edad", [60, 85], ids=["CP-22-60", "CP-22-85"])
def test_cp22_desde_60_anios_tiene_50_por_ciento_de_descuento(edad):
    assert calcular_precio_entrada(edad, TipoPase.REGULAR) == REGULAR / 2


def test_pase_vip_cuesta_mas_que_el_regular():
    assert (
        calcular_precio_entrada(30, TipoPase.VIP) == PRECIO_BASE[TipoPase.VIP]
    )
    assert PRECIO_BASE[TipoPase.VIP] > REGULAR


def test_descuento_por_edad_tambien_aplica_al_pase_vip():
    assert (
        calcular_precio_entrada(10, TipoPase.VIP)
        == PRECIO_BASE[TipoPase.VIP] / 2
    )
