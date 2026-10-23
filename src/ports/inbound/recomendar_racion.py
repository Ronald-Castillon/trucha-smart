"""Puerto de entrada: recomendación de ración diaria del lote (RF-07)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from src.domain.model.lectura_agua import LecturaAgua
from src.domain.model.lote import Lote
from src.domain.model.usuario import Usuario
from src.domain.service.recomendador_racion import Recomendacion


@dataclass(frozen=True)
class RecomendacionLote:
    lote: Lote
    peces_vivos: int
    lectura: LecturaAgua | None  # lectura de agua usada para los factores
    recomendacion: Recomendacion


class RecomendarRacion(Protocol):
    def recomendar(self, lote_id: int, solicitante: Usuario) -> RecomendacionLote: ...
