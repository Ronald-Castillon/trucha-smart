"""Puerto de salida: persistencia de alertas."""

from __future__ import annotations

from typing import Protocol

from src.domain.model.alerta import Alerta, EstadoAlerta
from src.domain.model.lectura_agua import Parametro
from src.domain.model.umbral import Nivel


class RepositorioAlerta(Protocol):
    def guardar(self, alerta: Alerta) -> Alerta: ...

    def por_id(self, alerta_id: int) -> Alerta | None: ...

    def abierta(self, estanque_id: int, parametro: Parametro, nivel: Nivel) -> Alerta | None:
        """Alerta ABIERTA del mismo estanque, parámetro y nivel (para no duplicar)."""
        ...

    def listar(
        self,
        estanque_id: int | None = None,
        estado: EstadoAlerta | None = None,
        limite: int | None = None,
    ) -> list[Alerta]:
        """De la más reciente a la más antigua."""
        ...
