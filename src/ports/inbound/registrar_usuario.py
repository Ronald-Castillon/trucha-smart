"""Puerto de entrada: registro y gestión de usuarios (RF-01)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from src.domain.model.usuario import Rol, Usuario


@dataclass(frozen=True)
class ComandoRegistrarUsuario:
    nombre_usuario: str
    nombre_completo: str
    password: str
    rol: Rol


class RegistrarUsuario(Protocol):
    def registrar(self, comando: ComandoRegistrarUsuario, solicitante: Usuario) -> Usuario: ...

    def listar(self, solicitante: Usuario) -> list[Usuario]: ...
