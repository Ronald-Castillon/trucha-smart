"""Puerto de salida: generación de archivos de reporte (CSV, PDF)."""

from __future__ import annotations

from typing import Protocol

from src.ports.inbound.exportar_reporte import Reporte


class GeneradorReportes(Protocol):
    def csv(self, reporte: Reporte) -> bytes: ...

    def pdf(self, reporte: Reporte) -> bytes: ...
