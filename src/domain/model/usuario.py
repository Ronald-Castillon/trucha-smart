"""Usuario, roles y política de permisos (RF-01, brecha B-04)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from src.domain.errores import ErrorValidacion, PermisoDenegado


class Rol(StrEnum):
    ADMINISTRADOR = "ADMINISTRADOR"
    PISCICULTOR = "PISCICULTOR"
    OPERARIO = "OPERARIO"


class Permiso(StrEnum):
    CONSULTAR = "CONSULTAR"
    REGISTRAR_LECTURA = "REGISTRAR_LECTURA"
    REGISTRAR_ALIMENTACION = "REGISTRAR_ALIMENTACION"
    ATENDER_ALERTA = "ATENDER_ALERTA"
    GESTIONAR_ESTANQUES = "GESTIONAR_ESTANQUES"
    GESTIONAR_REPORTES = "GESTIONAR_REPORTES"
    GESTIONAR_USUARIOS = "GESTIONAR_USUARIOS"


_OPERARIO = frozenset(
    {
        Permiso.CONSULTAR,
        Permiso.REGISTRAR_LECTURA,
        Permiso.REGISTRAR_ALIMENTACION,
        Permiso.ATENDER_ALERTA,
    }
)
_PISCICULTOR = _OPERARIO | {Permiso.GESTIONAR_ESTANQUES, Permiso.GESTIONAR_REPORTES}
_ADMINISTRADOR = _PISCICULTOR | {Permiso.GESTIONAR_USUARIOS}

PERMISOS_POR_ROL: dict[Rol, frozenset[Permiso]] = {
    Rol.OPERARIO: _OPERARIO,
    Rol.PISCICULTOR: frozenset(_PISCICULTOR),
    Rol.ADMINISTRADOR: frozenset(_ADMINISTRADOR),
}

LONGITUD_MINIMA_PASSWORD = 8


@dataclass
class Usuario:
    nombre_usuario: str
    nombre_completo: str
    password_hash: str
    rol: Rol
    creado_en: datetime
    activo: bool = True
    id: int | None = None

    def puede(self, permiso: Permiso) -> bool:
        return self.activo and permiso in PERMISOS_POR_ROL[self.rol]

    def exigir(self, permiso: Permiso) -> None:
        if not self.puede(permiso):
            raise PermisoDenegado(
                f"El rol {self.rol.value} no tiene permiso para {permiso.value.lower()}"
            )


def validar_nombre_usuario(nombre: str) -> str:
    limpio = nombre.strip().lower()
    if not (3 <= len(limpio) <= 50) or not all(c.isalnum() or c in "._-" for c in limpio):
        raise ErrorValidacion(
            "nombre_usuario",
            "El nombre de usuario debe tener 3 a 50 caracteres (letras, números, . _ -)",
        )
    return limpio


def validar_password(password: str) -> None:
    if len(password) < LONGITUD_MINIMA_PASSWORD:
        raise ErrorValidacion(
            "password",
            f"La contraseña debe tener al menos {LONGITUD_MINIMA_PASSWORD} caracteres",
        )
