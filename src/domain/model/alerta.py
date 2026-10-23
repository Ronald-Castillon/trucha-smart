"""Alerta de calidad de agua y su atención (RF-04, brechas B-03 y B-06)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from src.domain.errores import Conflicto, ErrorValidacion
from src.domain.model.lectura_agua import Parametro
from src.domain.model.umbral import Nivel


class EstadoAlerta(StrEnum):
    ABIERTA = "ABIERTA"
    ATENDIDA = "ATENDIDA"


@dataclass
class Alerta:
    estanque_id: int
    lectura_id: int
    parametro: Parametro
    nivel: Nivel
    valor: float
    mensaje: str
    creada_en: datetime
    estado: EstadoAlerta = EstadoAlerta.ABIERTA
    atendida_por: int | None = None
    atendida_en: datetime | None = None
    observacion: str | None = None
    id: int | None = None

    def __post_init__(self) -> None:
        if self.nivel is Nivel.NORMAL:
            raise ErrorValidacion("nivel", "Una alerta debe ser de PRECAUCIÓN o CRÍTICA")

    @property
    def abierta(self) -> bool:
        return self.estado is EstadoAlerta.ABIERTA

    def atender(self, usuario_id: int, momento: datetime, observacion: str | None = None) -> None:
        """Registra quién atendió la alerta y cuándo (B-06)."""
        if not self.abierta:
            raise Conflicto(f"La alerta {self.id} ya fue atendida")
        observacion = (observacion or "").strip() or None
        if observacion and len(observacion) > 255:
            raise ErrorValidacion("observacion", "La observación admite máximo 255 caracteres")
        self.estado = EstadoAlerta.ATENDIDA
        self.atendida_por = usuario_id
        self.atendida_en = momento
        self.observacion = observacion
