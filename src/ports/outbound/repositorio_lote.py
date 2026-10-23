"""Puerto de salida: persistencia de lotes."""

from __future__ import annotations

from typing import Protocol

from src.domain.model.lote import Lote


class RepositorioLote(Protocol):
    def guardar(self, lote: Lote) -> Lote: ...

    def por_id(self, lote_id: int) -> Lote | None: ...

    def por_codigo(self, codigo: str) -> Lote | None: ...

    def activo_de(self, estanque_id: int) -> Lote | None: ...

    def de_estanque(self, estanque_id: int) -> list[Lote]: ...
