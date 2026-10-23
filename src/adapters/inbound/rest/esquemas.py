"""Esquemas Pydantic de la API (solo en el adaptador REST)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from src.domain.model.usuario import Rol, Usuario

# --------------------------------------------------------------------------- usuarios


class LoginEntrada(BaseModel):
    nombre_usuario: str = Field(examples=["operario"])
    password: str = Field(examples=["Oper123!"])


class UsuarioSalida(BaseModel):
    id: int
    nombre_usuario: str
    nombre_completo: str
    rol: Rol
    activo: bool
    creado_en: datetime

    @classmethod
    def de(cls, u: Usuario) -> UsuarioSalida:
        return cls(
            id=u.id,
            nombre_usuario=u.nombre_usuario,
            nombre_completo=u.nombre_completo,
            rol=u.rol,
            activo=u.activo,
            creado_en=u.creado_en,
        )


class TokenSalida(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expira_en_segundos: int
    usuario: UsuarioSalida


class UsuarioEntrada(BaseModel):
    nombre_usuario: str
    nombre_completo: str
    password: str
    rol: Rol
