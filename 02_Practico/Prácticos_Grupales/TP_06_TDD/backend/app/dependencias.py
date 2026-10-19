import logging
import os
import sqlite3
from functools import lru_cache
from pathlib import Path

import httpx
from dotenv import load_dotenv

from app.adaptadores.notificador import NotificadorEmailLog, NotificadorSMTP
from app.adaptadores.pasarela_pago import PasarelaMercadoPago
from app.adaptadores.reloj import RelojSistema
from app.adaptadores.repositorios_sqlite import (
    RepositorioComprasSQLite,
    RepositorioUsuariosSQLite,
)
from app.mercado_pago_simulado.api import (
    PREFIJO_API_SIMULADA,
    transporte_en_proceso,
)
from app.mercado_pago_simulado.nucleo import (
    TOKEN_SIMULADO,
    MercadoPagoSimulado,
)
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


def crear_pasarela_pago(configuracion, simulador=None, cliente=None):
    access_token = configuracion.get("MP_ACCESS_TOKEN")
    url_retorno = configuracion.get("URL_PUBLICA", URL_PUBLICA_POR_DEFECTO)
    if access_token:
        return PasarelaMercadoPago(
            access_token,
            url_retorno,
            cliente,
            email_comprador_prueba=configuracion.get(
                "MP_EMAIL_COMPRADOR_PRUEBA"
            ),
        )
    logger.warning("Sin MP_ACCESS_TOKEN: se usa el Mercado Pago simulado")
    simulador = simulador or obtener_mercado_pago_simulado()
    # La misma pasarela que en el modo real, hablándole al simulador
    # dentro del mismo proceso.
    return PasarelaMercadoPago(
        TOKEN_SIMULADO,
        url_retorno,
        httpx.Client(transport=transporte_en_proceso(simulador)),
        url_api=url_retorno.rstrip("/") + PREFIJO_API_SIMULADA,
    )


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
