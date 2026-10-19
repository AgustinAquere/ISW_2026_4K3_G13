from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.adaptadores.reloj import RelojSistema
from app.dependencias import obtener_reloj, obtener_servicio_compra
from app.dominio.calendario import fechas_disponibles
from app.dominio.errores import (
    CompraInvalidaError,
    CompraNoEncontradaError,
    PagoNoDisponibleError,
    UsuarioNoRegistradoError,
)
from app.dominio.modelos import SolicitudCompra
from app.dominio.precios import calcular_precio_entrada
from app.schemas import (
    CompraRequest,
    CompraResponse,
    ConfirmacionPagoRequest,
    CotizacionRequest,
    CotizacionResponse,
    FechasDisponiblesResponse,
    VerificacionPagoResponse,
)
from app.servicios.compra_service import ServicioCompra

router = APIRouter()


def usuario_en_sesion(
    x_usuario_email: Annotated[str | None, Header()] = None,
):
    # Sesión simulada (FAQ 19): la cabecera representa al usuario logueado.
    if x_usuario_email is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Debe iniciar sesión"
        )
    return x_usuario_email


@router.post(
    "/compras",
    response_model=CompraResponse,
    status_code=status.HTTP_201_CREATED,
)
def comprar_entradas(
    compra: CompraRequest,
    servicio: Annotated[ServicioCompra, Depends(obtener_servicio_compra)],
    email_usuario: Annotated[str, Depends(usuario_en_sesion)],
):
    solicitud = SolicitudCompra(
        email_usuario=email_usuario, **compra.model_dump()
    )
    try:
        resultado = servicio.comprar(solicitud)
    except UsuarioNoRegistradoError as error:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Usuario no registrado"
        ) from error
    except CompraInvalidaError as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error)) from error
    except PagoNoDisponibleError as error:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            "No se pudo iniciar el pago con Mercado Pago. "
            "Intentá de nuevo más tarde.",
        ) from error
    return CompraResponse.desde_compra(resultado)


@router.post("/compras/{id_compra}/pago", response_model=CompraResponse)
def confirmar_pago(
    id_compra: int,
    confirmacion: ConfirmacionPagoRequest,
    servicio: Annotated[ServicioCompra, Depends(obtener_servicio_compra)],
    email_usuario: Annotated[str, Depends(usuario_en_sesion)],
):
    try:
        compra = servicio.confirmar_pago(
            email_usuario, id_compra, confirmacion.id_pago
        )
    except CompraNoEncontradaError as error:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Compra no encontrada"
        ) from error
    except CompraInvalidaError as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error)) from error
    except PagoNoDisponibleError as error:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            "No se pudo consultar el pago con Mercado Pago. "
            "Intentá de nuevo más tarde.",
        ) from error
    return CompraResponse.desde_compra(compra)


@router.post(
    "/compras/{id_compra}/verificacion-de-pago",
    response_model=VerificacionPagoResponse,
)
def verificar_pago(
    id_compra: int,
    servicio: Annotated[ServicioCompra, Depends(obtener_servicio_compra)],
    email_usuario: Annotated[str, Depends(usuario_en_sesion)],
):
    try:
        compra, pago = servicio.verificar_pago(email_usuario, id_compra)
    except CompraNoEncontradaError as error:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Compra no encontrada"
        ) from error
    except CompraInvalidaError as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error)) from error
    except PagoNoDisponibleError as error:
        raise HTTPException(
            status.HTTP_502_BAD_GATEWAY,
            "No se pudo consultar el pago con Mercado Pago. "
            "Intentá de nuevo más tarde.",
        ) from error
    return VerificacionPagoResponse.desde_verificacion(compra, pago)


@router.get("/fechas-disponibles", response_model=FechasDisponiblesResponse)
def consultar_fechas_disponibles(
    reloj: Annotated[RelojSistema, Depends(obtener_reloj)],
):
    return {"fechas": fechas_disponibles(reloj.ahora())}


@router.post("/cotizacion", response_model=CotizacionResponse)
def cotizar(cotizacion: CotizacionRequest):
    total = sum(
        calcular_precio_entrada(edad, cotizacion.tipo_pase)
        for edad in cotizacion.edades
    )
    return {"total": total}
