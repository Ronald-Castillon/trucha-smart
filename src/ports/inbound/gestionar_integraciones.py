"""Puerto de entrada: claves de integración y consulta externa de datos (RF-09)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Protocol

from src.domain.model.clave_integracion import ClaveIntegracion
from src.domain.model.estanque import Estanque
from src.domain.model.lectura_agua import LecturaAgua, Parametro
from src.domain.model.umbral import Nivel
from src.domain.model.usuario import Usuario


@dataclass(frozen=True)
class ClaveCreada:
    clave: ClaveIntegracion
    secreto: str  # se muestra una sola vez


@dataclass(frozen=True)
class EstadoExterno:
    estanque: Estanque
    ultima_lectura: LecturaAgua | None
    niveles: dict[Parametro, Nivel]
    alertas_abiertas: int


class GestionarIntegraciones(Protocol):
    def crear(self, nombre: str, solicitante: Usuario) -> ClaveCreada: ...

    def listar(self, solicitante: Usuario) -> list[ClaveIntegracion]: ...

    def revocar(self, clave_id: int, solicitante: Usuario) -> ClaveIntegracion: ...

    def autenticar(self, secreto: str | None) -> ClaveIntegracion:
        """Devuelve la clave activa o lanza ClaveInvalida; registra el último uso."""
        ...

    def estado_estanques(self, clave: ClaveIntegracion) -> list[EstadoExterno]: ...

    def lecturas(
        self, clave: ClaveIntegracion, estanque_id: int, desde: date | None, hasta: date | None
    ) -> list[LecturaAgua]: ...
