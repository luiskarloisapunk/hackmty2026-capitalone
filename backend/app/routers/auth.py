from __future__ import annotations

import jwt
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr, Field

from app.services.auth import (
    crear_token_acceso,
    decodificar_token_acceso,
    hashear_password,
    verificar_password,
)
from app.services import negocio_service
from app.services.db import db

usuarios_collection = db["usuarios"]

router = APIRouter(prefix="/api/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=True)


# ---------------------------------------------------------------------------
# Esquemas
# ---------------------------------------------------------------------------


class RegistroRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    nombre: str = Field(min_length=1)
    nombre_negocio: str = Field(min_length=1)
    tiene_historial: bool = Field(
        default=False,
        description="Si ya lleva registro de sus finanzas. Si es true, sube su CSV después del registro.",
    )
    plantilla_id: str | None = Field(
        default=None,
        description="Giro con el que arranca cuando no tiene historial propio.",
    )


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UsuarioOut(BaseModel):
    id: str
    email: str
    nombre: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    usuario: UsuarioOut


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/registro", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def registrar_usuario(body: RegistroRequest) -> TokenResponse:
    existente = await usuarios_collection.find_one({"email": body.email})
    if existente:
        raise HTTPException(status_code=409, detail="Ya existe una cuenta con ese correo")

    documento = {
        "email": body.email,
        "nombre": body.nombre,
        "password_hash": hashear_password(body.password),
    }
    resultado = await usuarios_collection.insert_one(documento)
    usuario_id = str(resultado.inserted_id)

    await negocio_service.crear_perfil(
        usuario_id=usuario_id,
        nombre_negocio=body.nombre_negocio,
        plantilla_id=body.plantilla_id,
        tiene_historial=body.tiene_historial,
    )

    token = crear_token_acceso(subject=usuario_id)
    return TokenResponse(
        access_token=token,
        usuario=UsuarioOut(id=usuario_id, email=body.email, nombre=body.nombre),
    )


@router.post("/login", response_model=TokenResponse)
async def iniciar_sesion(body: LoginRequest) -> TokenResponse:
    usuario = await usuarios_collection.find_one({"email": body.email})
    if not usuario or not verificar_password(body.password, usuario["password_hash"]):
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")

    usuario_id = str(usuario["_id"])
    token = crear_token_acceso(subject=usuario_id)
    return TokenResponse(
        access_token=token,
        usuario=UsuarioOut(id=usuario_id, email=usuario["email"], nombre=usuario["nombre"]),
    )


async def obtener_usuario_actual(token: str = Depends(oauth2_scheme)) -> UsuarioOut:
    credenciales_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decodificar_token_acceso(token)
        usuario_id = payload.get("sub")
        if usuario_id is None:
            raise credenciales_invalidas
    except jwt.PyJWTError:
        raise credenciales_invalidas

    try:
        usuario = await usuarios_collection.find_one({"_id": ObjectId(usuario_id)})
    except InvalidId:
        raise credenciales_invalidas

    if usuario is None:
        raise credenciales_invalidas

    return UsuarioOut(id=str(usuario["_id"]), email=usuario["email"], nombre=usuario["nombre"])


@router.get("/me", response_model=UsuarioOut)
async def usuario_actual(usuario: UsuarioOut = Depends(obtener_usuario_actual)) -> UsuarioOut:
    return usuario
