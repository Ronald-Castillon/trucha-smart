"""Puerto de entrada: registro y consulta básica de lecturas de calidad de agua (RF-03)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from src.domain.model.lectura_agua import FuenteLectura, LecturaAgua
from src.domain.model.usuario import Usuario


@dataclass(frozen=True)
class ComandoRegistrarLectura:
    estanque_id: int
    temperatura_c: float
    oxigeno_mg_l: float
    ph: float
    fuente: FuenteLectura = FuenteLectura.MANUAL
    medido_en: datetime | None = None  # None = ahora


class RegistrarLectura(Protocol):
    def registrar(self, comando: ComandoRegistrarLectura, solicitante: Usuario) -> LecturaAgua: ...

    def ultima(self, estanque_id: int, solicitante: Usuario) -> LecturaAgua | None: ...

    def recientes(
        self, estanque_id: int, solicitante: Usuario, limite: int = 20
    ) -> list[LecturaAgua]: ...
