"""Puerto de salida: persistencia de estanques."""

from __future__ import annotations

from typing import Protocol

from src.domain.model.estanque import Estanque


class RepositorioEstanque(Protocol):
    def guardar(self, estanque: Estanque) -> Estanque: ...

    def por_id(self, estanque_id: int) -> Estanque | None: ...

    def por_nombre(self, nombre: str) -> Estanque | None: ...

    def listar(self, solo_activos: bool = True) -> list[Estanque]: ...
