"""Puerto de entrada: exportación de reportes de producción y calidad de agua (RF-08)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from typing import Protocol

from src.domain.model.lectura_agua import Parametro
from src.domain.model.umbral import Nivel
from src.domain.model.usuario import Usuario


class TipoReporte(StrEnum):
    CALIDAD_AGUA = "calidad-agua"
    PRODUCCION = "produccion"


class FormatoReporte(StrEnum):
    CSV = "csv"
    PDF = "pdf"


@dataclass(frozen=True)
class FilaCalidad:
    estanque: str
    medido_en: datetime
    temperatura_c: float
    oxigeno_mg_l: float
    ph: float
    fuente: str
    niveles: dict[Parametro, Nivel]


@dataclass(frozen=True)
class ResumenCalidadEstanque:
    estanque: str
    lecturas: int
    temperatura: tuple[float, float, float] | None  # (mín, promedio, máx)
    oxigeno: tuple[float, float, float] | None
    ph: tuple[float, float, float] | None
    alertas_precaucion: int
    alertas_criticas: int
    alertas_atendidas: int


@dataclass(frozen=True)
class FilaProduccion:
    estanque: str
    lote: str
    fecha_siembra: date
    activo: bool
    peces_sembrados: int
    mortalidad_periodo: int
    mortalidad_total: int
    peces_vivos: int
    peso_medio_actual_g: float
    biomasa_kg: float
    alimento_periodo_kg: float
    alimento_total_kg: float
    fcr: str


@dataclass(frozen=True)
class Reporte:
    tipo: TipoReporte
    titulo: str
    desde: date
    hasta: date
    generado_en: datetime
    generado_por: str
    filas_calidad: list[FilaCalidad]
    resumen_calidad: list[ResumenCalidadEstanque]
    filas_produccion: list[FilaProduccion]


@dataclass(frozen=True)
class ArchivoReporte:
    nombre: str
    tipo_contenido: str
    contenido: bytes


class ExportarReporte(Protocol):
    def armar(self, tipo: TipoReporte, desde: date, hasta: date, solicitante: Usuario) -> Reporte:
        """Datos del reporte (vista previa), sin generar el archivo."""
        ...

    def exportar(
        self,
        tipo: TipoReporte,
        formato: FormatoReporte,
        desde: date,
        hasta: date,
        solicitante: Usuario,
    ) -> ArchivoReporte: ...
