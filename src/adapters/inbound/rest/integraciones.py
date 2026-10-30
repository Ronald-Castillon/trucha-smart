"""Routers de integración externa (RF-09): administración de claves y API de solo lectura."""

from __future__ import annotations

from datetime import date, datetime

from fastapi import APIRouter, Depends, Request, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field

from src.adapters.inbound.rest.dependencias import Contenedor, contenedor, usuario_actual
from src.adapters.inbound.rest.errores import RESPUESTAS_ERROR
from src.domain.model.clave_integracion import ClaveIntegracion
from src.domain.model.lectura_agua import Parametro
from src.domain.model.umbral import Nivel
from src.domain.model.usuario import Usuario

admin = APIRouter(prefix="/api/integraciones", tags=["integraciones"], responses=RESPUESTAS_ERROR)
externa = APIRouter(
    prefix="/api/externa/v1",
    tags=["API externa (claves de integración)"],
    responses=RESPUESTAS_ERROR,
)

_cabecera_clave = APIKeyHeader(
    name="X-API-Key",
    auto_error=False,
    description="Clave de integración emitida por un Administrador",
)


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


class ClaveEntrada(BaseModel):
    nombre: str = Field(examples=["ERP de la piscigranja"])


class ClaveSalida(BaseModel):
    id: int
    nombre: str
    prefijo: str
    activa: bool
    creada_en: datetime
    ultimo_uso: datetime | None

    @classmethod
    def de(cls, c: ClaveIntegracion) -> ClaveSalida:
        return cls(**{k: getattr(c, k) for k in cls.model_fields})


class ClaveCreadaSalida(ClaveSalida):
    clave: str = Field(description="Se muestra una sola vez; guárdela en un lugar seguro")


class LecturaExterna(BaseModel):
    medido_en: datetime
    temperatura_c: float
    oxigeno_mg_l: float
    ph: float


class EstanqueExterno(BaseModel):
    id: int
    nombre: str
    tipo: str
    ultima_lectura: LecturaExterna | None
    niveles: dict[Parametro, Nivel]
    alertas_abiertas: int


def _lectura(x) -> LecturaExterna:
    return LecturaExterna(
        medido_en=x.medido_en, temperatura_c=x.temperatura_c, oxigeno_mg_l=x.oxigeno_mg_l, ph=x.ph
    )


# --------------------------------------------------------------------------- administración


@admin.get("", response_model=list[ClaveSalida])
def listar_claves(
    usuario: Usuario = Depends(usuario_actual), c: Contenedor = Depends(contenedor)
) -> list[ClaveSalida]:
    return [ClaveSalida.de(x) for x in c.integraciones.listar(usuario)]


@admin.post("", response_model=ClaveCreadaSalida, status_code=201)
def crear_clave(
    datos: ClaveEntrada,
    request: Request,
    usuario: Usuario = Depends(usuario_actual),
    c: Contenedor = Depends(contenedor),
) -> ClaveCreadaSalida:
    """Emite una clave de integración (solo Administrador). La clave se devuelve una única vez."""
    creada = c.integraciones.crear(datos.nombre, usuario, _ip(request))
    c.confirmar()
    return ClaveCreadaSalida(**ClaveSalida.de(creada.clave).model_dump(), clave=creada.secreto)


@admin.delete("/{clave_id}", response_model=ClaveSalida)
def revocar_clave(
    clave_id: int,
    request: Request,
    usuario: Usuario = Depends(usuario_actual),
    c: Contenedor = Depends(contenedor),
) -> ClaveSalida:
    revocada = c.integraciones.revocar(clave_id, usuario, _ip(request))
    c.confirmar()
    return ClaveSalida.de(revocada)


# --------------------------------------------------------------------------- consumo externo


def clave_actual(
    request: Request,
    secreto: str | None = Security(_cabecera_clave),
    c: Contenedor = Depends(contenedor),
) -> ClaveIntegracion:
    ip = _ip(request)
    try:
        clave = c.integraciones.autenticar(secreto, ip)
    finally:
        c.confirmar()  # registra el último uso o el rechazo en la bitácora (RF-11)
    return clave


@externa.get("/estanques", response_model=list[EstanqueExterno])
def estanques_externos(
    clave: ClaveIntegracion = Depends(clave_actual), c: Contenedor = Depends(contenedor)
) -> list[EstanqueExterno]:
    """Estado actual de los estanques activos: última lectura, nivel por parámetro y alertas."""
    return [
        EstanqueExterno(
            id=e.estanque.id,
            nombre=e.estanque.nombre,
            tipo=e.estanque.tipo.value,
            ultima_lectura=_lectura(e.ultima_lectura) if e.ultima_lectura else None,
            niveles=e.niveles,
            alertas_abiertas=e.alertas_abiertas,
        )
        for e in c.integraciones.estado_estanques(clave)
    ]


@externa.get("/estanques/{estanque_id}/lecturas", response_model=list[LecturaExterna])
def lecturas_externas(
    estanque_id: int,
    desde: date | None = None,
    hasta: date | None = None,
    clave: ClaveIntegracion = Depends(clave_actual),
    c: Contenedor = Depends(contenedor),
) -> list[LecturaExterna]:
    """Lecturas del estanque entre `desde` y `hasta` (UTC, inclusivas; máximo 31 días)."""
    return [_lectura(x) for x in c.integraciones.lecturas(clave, estanque_id, desde, hasta)]
