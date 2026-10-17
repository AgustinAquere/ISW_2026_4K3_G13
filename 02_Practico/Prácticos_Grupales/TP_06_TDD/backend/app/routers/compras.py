from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.dependencias import obtener_servicio_compra
from app.dominio.errores import CompraInvalidaError, UsuarioNoRegistradoError
from app.dominio.modelos import SolicitudCompra
from app.schemas import CompraRequest, CompraResponse
from app.servicios.compra_service import ServicioCompra

router = APIRouter()


@router.post(
    "/compras",
    response_model=CompraResponse,
    status_code=status.HTTP_201_CREATED,
)
def comprar_entradas(
    compra: CompraRequest,
    servicio: Annotated[ServicioCompra, Depends(obtener_servicio_compra)],
    x_usuario_email: Annotated[str | None, Header()] = None,
):
    if x_usuario_email is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Debe iniciar sesión"
        )
    solicitud = SolicitudCompra(
        email_usuario=x_usuario_email, **compra.model_dump()
    )
    try:
        resultado = servicio.comprar(solicitud)
    except UsuarioNoRegistradoError as error:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "Usuario no registrado"
        ) from error
    except CompraInvalidaError as error:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(error)) from error
    return CompraResponse.desde_compra(resultado)
