import logging
import sqlite3
from functools import lru_cache
from pathlib import Path

from app.adaptadores.notificador import NotificadorEmailLog
from app.adaptadores.pasarela_pago import PasarelaMercadoPagoSimulada
from app.adaptadores.reloj import RelojSistema
from app.adaptadores.repositorios_sqlite import (
    RepositorioComprasSQLite,
    RepositorioUsuariosSQLite,
)
from app.servicios.compra_service import ServicioCompra

RUTA_BASE_DE_DATOS = Path(__file__).resolve().parent.parent / "ecoharmony.db"

# Usuario de demostración: el registro pertenece a otra User Story.
USUARIOS_REGISTRADOS = ["visitante@ecoharmony.com"]


@lru_cache
def obtener_servicio_compra():
    # FastAPI atiende cada solicitud en un hilo distinto del que abrió la
    # conexión, por eso se habilita su uso desde otros hilos.
    conexion = sqlite3.connect(RUTA_BASE_DE_DATOS, check_same_thread=False)
    return ServicioCompra(
        reloj=RelojSistema(),
        usuarios=RepositorioUsuariosSQLite(conexion, USUARIOS_REGISTRADOS),
        compras=RepositorioComprasSQLite(conexion),
        notificador=NotificadorEmailLog(logging.getLogger("uvicorn.error")),
        pasarela_pago=PasarelaMercadoPagoSimulada(),
    )
