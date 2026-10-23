"""Emisión y validación de tokens JWT (HS256) para sesiones web y API."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt

from src.domain.model.usuario import Usuario


class ServicioTokens:
    ALGORITMO = "HS256"

    def __init__(self, secreto: str, expira_minutos: int) -> None:
        self._secreto = secreto
        self._expira = timedelta(minutes=expira_minutos)

    @property
    def expira_segundos(self) -> int:
        return int(self._expira.total_seconds())

    def emitir(self, usuario: Usuario) -> str:
        ahora = datetime.now(UTC)
        datos = {
            "sub": str(usuario.id),
            "rol": usuario.rol.value,
            "iat": ahora,
            "exp": ahora + self._expira,
        }
        return jwt.encode(datos, self._secreto, algorithm=self.ALGORITMO)

    def usuario_id(self, token: str) -> int | None:
        """Devuelve el id del usuario del token o None si es inválido o expiró."""
        try:
            datos = jwt.decode(token, self._secreto, algorithms=[self.ALGORITMO])
            return int(datos["sub"])
        except (jwt.PyJWTError, KeyError, ValueError):
            return None
