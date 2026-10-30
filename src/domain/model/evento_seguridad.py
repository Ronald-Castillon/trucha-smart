"""Evento de la bitácora de seguridad (RF-11, OWASP A09). Nunca guarda contraseñas ni claves."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class TipoEvento(StrEnum):
    LOGIN_EXITOSO = "LOGIN_EXITOSO"
    LOGIN_FALLIDO = "LOGIN_FALLIDO"
    CUENTA_BLOQUEADA = "CUENTA_BLOQUEADA"
    LOGIN_RECHAZADO_BLOQUEO = "LOGIN_RECHAZADO_BLOQUEO"
    CLAVE_CREADA = "CLAVE_CREADA"
    CLAVE_REVOCADA = "CLAVE_REVOCADA"
    CLAVE_RECHAZADA = "CLAVE_RECHAZADA"


DESCRIPCION_EVENTO: dict[TipoEvento, str] = {
    TipoEvento.LOGIN_EXITOSO: "Inicio de sesión exitoso",
    TipoEvento.LOGIN_FALLIDO: "Inicio de sesión fallido",
    TipoEvento.CUENTA_BLOQUEADA: "Cuenta bloqueada por intentos fallidos",
    TipoEvento.LOGIN_RECHAZADO_BLOQUEO: "Intento con la cuenta bloqueada",
    TipoEvento.CLAVE_CREADA: "Clave de integración creada",
    TipoEvento.CLAVE_REVOCADA: "Clave de integración revocada",
    TipoEvento.CLAVE_RECHAZADA: "Clave de integración rechazada",
}


@dataclass
class EventoSeguridad:
    tipo: TipoEvento
    momento: datetime
    nombre_usuario: str | None = None
    usuario_id: int | None = None
    ip: str | None = None
    detalle: str = ""
    id: int | None = None

    @property
    def descripcion(self) -> str:
        return DESCRIPCION_EVENTO[self.tipo]
