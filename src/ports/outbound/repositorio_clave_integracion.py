"""Puerto de salida: persistencia de claves de integración."""

from __future__ import annotations

from typing import Protocol

from src.domain.model.clave_integracion import ClaveIntegracion


class RepositorioClaveIntegracion(Protocol):
    def guardar(self, clave: ClaveIntegracion) -> ClaveIntegracion: ...

    def por_id(self, clave_id: int) -> ClaveIntegracion | None: ...

    def por_hash(self, hash_clave: str) -> ClaveIntegracion | None: ...

    def listar(self) -> list[ClaveIntegracion]: ...
