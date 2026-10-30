"""Clave de integración para sistemas externos (RF-09).

La clave completa solo se conoce al crearla; se guarda su huella SHA-256 y un prefijo visible
para identificarla. Generación con `secrets` (aleatoriedad criptográfica, OWASP A02).
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import datetime

from src.domain.errores import ErrorValidacion

PREFIJO_CLAVE = "ts_"
LARGO_PREFIJO_VISIBLE = 11


def huella(clave: str) -> str:
    return hashlib.sha256(clave.encode("utf-8")).hexdigest()


def generar_clave() -> str:
    return PREFIJO_CLAVE + secrets.token_urlsafe(32)


@dataclass
class ClaveIntegracion:
    nombre: str
    prefijo: str
    hash_clave: str
    creada_en: datetime
    creada_por: int | None = None
    activa: bool = True
    ultimo_uso: datetime | None = None
    id: int | None = None

    def __post_init__(self) -> None:
        self.nombre = self.nombre.strip()
        if not (3 <= len(self.nombre) <= 80):
            raise ErrorValidacion(
                "nombre", "El nombre de la integración debe tener 3 a 80 caracteres"
            )

    @classmethod
    def nueva(
        cls, nombre: str, creada_por: int | None, momento: datetime
    ) -> tuple[ClaveIntegracion, str]:
        """Devuelve la entidad y la clave en claro (que no se vuelve a mostrar)."""
        clave = generar_clave()
        entidad = cls(
            nombre=nombre,
            prefijo=clave[:LARGO_PREFIJO_VISIBLE],
            hash_clave=huella(clave),
            creada_en=momento,
            creada_por=creada_por,
        )
        return entidad, clave

    def corresponde(self, clave: str) -> bool:
        return self.activa and hmac.compare_digest(self.hash_clave, huella(clave))

    def revocar(self) -> None:
        self.activa = False
