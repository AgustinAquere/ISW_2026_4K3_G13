import logging
import os
import sqlite3
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

from app.adaptadores.notificador import NotificadorEmailLog, NotificadorSMTP
from app.adaptadores.pasarela_pago import (
    PasarelaMercadoPago,
    PasarelaMercadoPagoSimulada,
)
from app.adaptadores.reloj import RelojSistema
from app.adaptadores.repositorios_sqlite import (
    RepositorioComprasSQLite,
    RepositorioUsuariosSQLite,
)
from app.mercado_pago_simulado.nucleo import MercadoPagoSimulado
from app.servicios.compra_service import ServicioCompra

RUTA_BACKEND = Path(__file__).resolve().parent.parent
RUTA_BASE_DE_DATOS = RUTA_BACKEND / "ecoharmony.db"

# Credenciales de Mercado Pago y SMTP: ver .env.example.
load_dotenv(RUTA_BACKEND / ".env")

# Usuario de demostración: el registro pertenece a otra User Story.
USUARIO_DE_DEMOSTRACION = "visitante@ecoharmony.com"
URL_PUBLICA_POR_DEFECTO = "http://127.0.0.1:8000/"

logger = logging.getLogger("uvicorn.error")


def usuarios_registrados(configuracion):
    emails = configuracion.get("USUARIOS_REGISTRADOS", USUARIO_DE_DEMOSTRACION)
    return [email.strip() for email in emails.split(",") if email.strip()]


def crear_pasarela_pago(configuracion):
    access_token = configuracion.get("MP_ACCESS_TOKEN")
    if not access_token:
        logger.warning("Sin MP_ACCESS_TOKEN: se simula Mercado Pago")
        return PasarelaMercadoPagoSimulada()
    url_retorno = configuracion.get("URL_PUBLICA", URL_PUBLICA_POR_DEFECTO)
    return PasarelaMercadoPago(access_token, url_retorno)


def crear_notificador(configuracion):
    host = configuracion.get("SMTP_HOST")
    if not host:
        logger.warning("Sin SMTP_HOST: los mails se escriben en el log")
        return NotificadorEmailLog(logger)
    usuario = configuracion.get("SMTP_USUARIO", "")
    return NotificadorSMTP(
        host=host,
        puerto=int(configuracion.get("SMTP_PUERTO", "587")),
        usuario=usuario,
        contrasena=configuracion.get("SMTP_CONTRASENA", ""),
        remitente=configuracion.get("SMTP_REMITENTE", usuario),
        logger=logger,
    )


@lru_cache
def obtener_mercado_pago_simulado():
    # Uno solo por proceso: guarda en memoria las preferencias y los pagos
    # que comparten el checkout simulado y la pasarela.
    return MercadoPagoSimulado(
        os.environ.get("URL_PUBLICA", URL_PUBLICA_POR_DEFECTO)
    )


def obtener_reloj():
    return RelojSistema()


@lru_cache
def obtener_servicio_compra():
    # FastAPI atiende cada solicitud en un hilo distinto del que abrió la
    # conexión, por eso se habilita su uso desde otros hilos.
    conexion = sqlite3.connect(RUTA_BASE_DE_DATOS, check_same_thread=False)
    return ServicioCompra(
        reloj=RelojSistema(),
        usuarios=RepositorioUsuariosSQLite(
            conexion, usuarios_registrados(os.environ)
        ),
        compras=RepositorioComprasSQLite(conexion),
        notificador=crear_notificador(os.environ),
        pasarela_pago=crear_pasarela_pago(os.environ),
    )
