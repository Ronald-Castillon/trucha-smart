"""Puerto de entrada: gestión de estanques/jaulas y lotes (RF-02)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol

from src.domain.model.estanque import Estanque, TipoEstanque
from src.domain.model.lote import Lote
from src.domain.model.usuario import Usuario


@dataclass(frozen=True)
class DatosEstanque:
    nombre: str
    tipo: TipoEstanque
    volumen_m3: float | None = None
    ubicacion: str | None = None


@dataclass(frozen=True)
class ComandoSembrarLote:
    estanque_id: int
    codigo: str
    num_peces: int
    peso_medio_g: float
    fecha_siembra: date


class GestionarEstanque(Protocol):
    def crear(self, datos: DatosEstanque, solicitante: Usuario) -> Estanque: ...

    def actualizar(
        self, estanque_id: int, datos: DatosEstanque, solicitante: Usuario
    ) -> Estanque: ...

    def desactivar(self, estanque_id: int, solicitante: Usuario) -> None: ...

    def obtener(self, estanque_id: int, solicitante: Usuario) -> Estanque: ...

    def listar(self, solicitante: Usuario) -> list[Estanque]: ...

    def sembrar_lote(self, comando: ComandoSembrarLote, solicitante: Usuario) -> Lote: ...

    def lote_activo(self, estanque_id: int, solicitante: Usuario) -> Lote | None: ...

    def lotes_de(self, estanque_id: int, solicitante: Usuario) -> list[Lote]: ...

    def obtener_lote(self, lote_id: int, solicitante: Usuario) -> Lote: ...

    def actualizar_peso(self, lote_id: int, peso_medio_g: float, solicitante: Usuario) -> Lote: ...

    def cerrar_lote(self, lote_id: int, fecha: date, solicitante: Usuario) -> Lote: ...
