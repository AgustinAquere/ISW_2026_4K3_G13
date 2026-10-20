"""Registro simulado de usuarios, sin contraseña.

El registro real pertenece a otra User Story (FAQ 19). Permite mostrar
que solo un usuario registrado puede comprar (CP-07).
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from app.adaptadores.repositorios_sqlite import RepositorioUsuariosSQLite
from app.dependencias import obtener_usuarios

router = APIRouter()


class RegistroRequest(BaseModel):
    """Email que se registra."""

    email: Annotated[str, Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")]

    @field_validator("email", mode="before")
    @classmethod
    def normalizar(cls, email):
        """Quita los espacios del email y lo pasa a minúsculas."""
        return email.strip().lower() if isinstance(email, str) else email


class RegistroResponse(BaseModel):
    """Email registrado."""

    email: str


@router.post(
    "/usuarios",
    response_model=RegistroResponse,
    status_code=status.HTTP_201_CREATED,
)
def registrar_usuario(
    registro: RegistroRequest,
    usuarios: Annotated[RepositorioUsuariosSQLite, Depends(obtener_usuarios)],
):
    """Registra el email; responde 409 si ya estaba registrado."""
    if not usuarios.registrar(registro.email):
        raise HTTPException(
            status.HTTP_409_CONFLICT, "El email ya está registrado"
        )
    return {"email": registro.email}
