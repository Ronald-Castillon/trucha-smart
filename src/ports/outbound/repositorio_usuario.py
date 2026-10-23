"""Puerto de salida: persistencia de usuarios."""

from __future__ import annotations

from typing import Protocol

from src.domain.model.usuario import Usuario


class RepositorioUsuario(Protocol):
    def guardar(self, usuario: Usuario) -> Usuario: ...

    def por_id(self, usuario_id: int) -> Usuario | None: ...

    def por_nombre_usuario(self, nombre_usuario: str) -> Usuario | None: ...

    def listar(self) -> list[Usuario]: ...
