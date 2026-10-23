"""Puerto de entrada: alimentación, mortalidad y resumen de producción del lote (RF-06)."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from src.domain.model.registro_alimentacion import RegistroAlimentacion
from src.domain.model.registro_mortalidad import RegistroMortalidad
from src.domain.model.usuario import Usuario
from src.domain.service.calculadora_fcr import ResumenProduccion


class RegistrarAlimentacion(Protocol):
    def registrar_alimentacion(
        self,
        lote_id: int,
        cantidad_kg: float,
        solicitante: Usuario,
        registrado_en: datetime | None = None,
    ) -> RegistroAlimentacion: ...

    def registrar_mortalidad(
        self,
        lote_id: int,
        cantidad: int,
        causa: str | None,
        solicitante: Usuario,
        registrado_en: datetime | None = None,
    ) -> RegistroMortalidad: ...

    def produccion(self, lote_id: int, solicitante: Usuario) -> ResumenProduccion:
        """Biomasa, peces vivos y FCR ("no calculable" si la ganancia es 0)."""
        ...

    def alimentaciones(self, lote_id: int, solicitante: Usuario) -> list[RegistroAlimentacion]: ...

    def mortalidades(self, lote_id: int, solicitante: Usuario) -> list[RegistroMortalidad]: ...
