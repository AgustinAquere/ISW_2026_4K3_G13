"""Días y horarios en que se pueden comprar entradas."""

from datetime import time, timedelta

from app.dominio.errores import CompraInvalidaError

LUNES = 0
FERIADOS_CERRADO = {(1, 1), (12, 25)}  # (mes, día)
DIAS_MAXIMOS_DE_ANTICIPACION = 31
HORA_LIMITE_COMPRA_DIA_ACTUAL = time(17, 30)


def esta_abierto(fecha):
    """Indica si el parque abre: cierra los lunes, el 1/1 y el 25/12."""
    return (
        fecha.weekday() != LUNES
        and (fecha.month, fecha.day) not in FERIADOS_CERRADO
    )


def validar_fecha_visita(fecha_visita, ahora):
    """Valida la fecha de visita respecto de la fecha y hora actuales.

    Lanza CompraInvalidaError si la fecha es pasada, supera los 31 días
    de anticipación, es hoy después de las 17:30 o el parque cierra.
    """
    hoy = ahora.date()
    if fecha_visita < hoy:
        raise CompraInvalidaError("La fecha de visita no puede ser pasada")
    if fecha_visita > hoy + timedelta(days=DIAS_MAXIMOS_DE_ANTICIPACION):
        raise CompraInvalidaError(
            "La fecha de visita no puede superar los "
            f"{DIAS_MAXIMOS_DE_ANTICIPACION} días de anticipación"
        )
    if fecha_visita == hoy and ahora.time() > HORA_LIMITE_COMPRA_DIA_ACTUAL:
        raise CompraInvalidaError(
            "Las entradas para hoy se venden hasta las "
            f"{HORA_LIMITE_COMPRA_DIA_ACTUAL:%H:%M}"
        )
    if not esta_abierto(fecha_visita):
        raise CompraInvalidaError("El parque está cerrado en la fecha elegida")


def fechas_disponibles(ahora):
    """Lista las fechas válidas desde hoy hasta dentro de 31 días."""
    hoy = ahora.date()
    candidatas = (
        hoy + timedelta(days=dias)
        for dias in range(DIAS_MAXIMOS_DE_ANTICIPACION + 1)
    )
    return [fecha for fecha in candidatas if _es_valida(fecha, ahora)]


def _es_valida(fecha_visita, ahora):
    try:
        validar_fecha_visita(fecha_visita, ahora)
    except CompraInvalidaError:
        return False
    return True
