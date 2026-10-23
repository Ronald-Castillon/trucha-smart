"""Puerto de salida: hash y verificación de contraseñas."""

from __future__ import annotations

from typing import Protocol


class HasherPassword(Protocol):
    def hashear(self, password: str) -> str: ...

    def verificar(self, password: str, password_hash: str) -> bool: ...
