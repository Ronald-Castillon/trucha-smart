"""Puerto de entrada: autenticación de usuarios (RF-01)."""

from __future__ import annotations

from typing import Protocol

from src.domain.model.usuario import Usuario


class Autenticar(Protocol):
    def autenticar(self, nombre_usuario: str, password: str, ip: str | None = None) -> Usuario:
        """Devuelve el usuario o lanza CredencialesInvalidas / CuentaBloqueada (RF-11)."""
        ...

    def usuario_activo(self, usuario_id: int) -> Usuario | None:
        """Resuelve el usuario de una sesión ya emitida (None si no existe o está inactivo)."""
        ...
