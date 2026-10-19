"""Fechas de prueba calculadas a partir del día en que se ejecutan.

Las pruebas no usan fechas fijas: una fecha fija termina quedando en el
pasado o fuera de la ventana de compra, y la prueba falla con el paso del
tiempo aunque el sistema no haya cambiado. Cada fecha se busca a partir de
hoy según lo que necesita la prueba (por ejemplo, el próximo lunes).

Los días de apertura se escriben acá a partir del FAQ 1 del PO, sin usar el
código de la aplicación, para no elegir los datos de prueba con la misma
lógica que se está probando.
"""

from datetime import date, datetime, time, timedelta

LUNES = 0
FERIADOS = {(1, 1), (12, 25)}  # (mes, día), FAQ 1
UN_DIA = timedelta(days=1)


def abierto(fecha):
    return (
        fecha.weekday() != LUNES and (fecha.month, fecha.day) not in FERIADOS
    )


def primer_dia(desde, condicion):
    dia = desde
    while not condicion(dia):
        dia += UN_DIA
    return dia


def siguiente_dia_abierto(desde):
    return primer_dia(desde, abierto)


def proximo_feriado(mes, dia):
    feriado = date(HOY.year, mes, dia)
    if feriado <= HOY:
        feriado = date(HOY.year + 1, mes, dia)
    return feriado


def a_las(fecha, hora):
    return datetime.combine(fecha, hora)


def dd_mm_aaaa(fecha):
    return f"{fecha.day:02d}/{fecha.month:02d}/{fecha.year}"


def _sirve_como_hoy(dia):
    # El parque abre ese día, el anterior y a 31 días: así los valores límite
    # de CP-12 (ayer) y CP-16 (31 días) dependen de una sola regla.
    return (
        abierto(dia)
        and abierto(dia - UN_DIA)
        and abierto(dia + timedelta(days=31))
    )


# "Hoy" de las pruebas: el primer día desde la fecha real que cumple lo
# anterior (a lo sumo, unos pocos días después de la fecha real).
HOY = primer_dia(date.today(), _sirve_como_hoy)
AHORA = a_las(HOY, time(10, 0))

# Fecha de visita válida dentro de la ventana de compra. El día es mayor a 12
# para que dd/mm/aaaa y mm/dd/aaaa no coincidan al verificar el resumen.
FECHA_VISITA = primer_dia(
    HOY + UN_DIA, lambda dia: abierto(dia) and dia.day > 12
)
OTRA_FECHA_VISITA = siguiente_dia_abierto(FECHA_VISITA + UN_DIA)
LUNES_PROXIMO = primer_dia(HOY + UN_DIA, lambda dia: dia.weekday() == LUNES)
