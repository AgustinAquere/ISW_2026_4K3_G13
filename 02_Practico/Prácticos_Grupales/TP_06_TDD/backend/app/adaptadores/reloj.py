"""Reloj del sistema; las pruebas usan un reloj fijo."""

from datetime import datetime


class RelojSistema:
    """Da la fecha y la hora de la computadora."""

    def ahora(self):
        """Devuelve la fecha y la hora actuales."""
        return datetime.now()
