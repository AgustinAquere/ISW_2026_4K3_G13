import logging
from functools import lru_cache

from app.adaptadores.notificador import NotificadorEmailLog
from app.adaptadores.pasarela_pago import PasarelaMercadoPagoSimulada
from app.adaptadores.reloj import RelojSistema
from app.adaptadores.repositorios import (
    RepositorioComprasEnMemoria,
    RepositorioUsuariosEnMemoria,
)
from app.servicios.compra_service import ServicioCompra

# Usuario de demostración: el registro pertenece a otra User Story.
USUARIOS_REGISTRADOS = ["visitante@ecoharmony.com"]


@lru_cache
def obtener_servicio_compra():
    return ServicioCompra(
        reloj=RelojSistema(),
        usuarios=RepositorioUsuariosEnMemoria(USUARIOS_REGISTRADOS),
        compras=RepositorioComprasEnMemoria(),
        notificador=NotificadorEmailLog(logging.getLogger("uvicorn.error")),
        pasarela_pago=PasarelaMercadoPagoSimulada(),
    )
