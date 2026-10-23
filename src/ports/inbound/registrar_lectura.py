"""Puerto de entrada: registro y consulta básica de lecturas de calidad de agua (RF-03, RF-04)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol

from src.domain.model.alerta import Alerta
from src.domain.model.lectura_agua import FuenteLectura, LecturaAgua, Parametro
from src.domain.model.umbral import Nivel
from src.domain.model.usuario import Usuario
from src.domain.service.evaluador_calidad_agua import Evaluacion


@dataclass(frozen=True)
class ComandoRegistrarLectura:
    estanque_id: int
    temperatura_c: float
    oxigeno_mg_l: float
    ph: float
    fuente: FuenteLectura = FuenteLectura.MANUAL
    medido_en: datetime | None = None  # None = ahora


@dataclass(frozen=True)
class ResultadoRegistroLectura:
    lectura: LecturaAgua
    evaluaciones: list[Evaluacion]
    alertas_nuevas: list[Alerta] = field(default_factory=list)


@dataclass(frozen=True)
class EstadoCalidad:
    """Última lectura de un estanque con el nivel de cada parámetro y sus alertas abiertas."""

    lectura: LecturaAgua | None
    niveles: dict[Parametro, Nivel]
    alertas_abiertas: list[Alerta]


class RegistrarLectura(Protocol):
    def registrar(
        self, comando: ComandoRegistrarLectura, solicitante: Usuario
    ) -> ResultadoRegistroLectura: ...

    def ultima(self, estanque_id: int, solicitante: Usuario) -> LecturaAgua | None: ...

    def recientes(
        self, estanque_id: int, solicitante: Usuario, limite: int = 20
    ) -> list[LecturaAgua]: ...

    def estado(self, estanque_id: int, solicitante: Usuario) -> EstadoCalidad: ...
