"""Puerto de salida: persistencia de lecturas de calidad de agua."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from src.domain.model.lectura_agua import LecturaAgua


class RepositorioLectura(Protocol):
    def guardar(self, lectura: LecturaAgua) -> LecturaAgua: ...

    def ultima_de(self, estanque_id: int) -> LecturaAgua | None: ...

    def de_estanque(
        self,
        estanque_id: int,
        desde: datetime | None = None,
        hasta: datetime | None = None,
        limite: int | None = None,
    ) -> list[LecturaAgua]:
        """Lecturas del estanque en [desde, hasta], de la más reciente a la más antigua."""
        ...
