"""Router del riesgo estimado por el modelo entrenado (RF-12, ADR-007)."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from src.adapters.inbound.rest.dependencias import Contenedor, contenedor, usuario_actual
from src.adapters.inbound.rest.errores import RESPUESTAS_ERROR
from src.domain.model.usuario import Usuario
from src.ports.inbound.evaluar_riesgo_modelo import EvaluacionRiesgoModelo

router = APIRouter(prefix="/api", tags=["riesgo (modelo de IA)"], responses=RESPUESTAS_ERROR)


class FactorSalida(BaseModel):
    nombre: str
    aporte: float


class RiesgoModeloSalida(BaseModel):
    estanque_id: int
    estanque: str
    nivel: str = Field(description="DATOS_INSUFICIENTES, YA_CRITICO, BAJO, MEDIO o ALTO")
    probabilidad: float | None = Field(description="Probabilidad de evento crítico en 6 h (0–1)")
    factores: list[FactorSalida] = Field(description="Características que más empujan al riesgo")
    version_modelo: str
    puntos: int
    basada_en_hasta: datetime | None
    mensaje: str
    aviso: str = (
        "Prototipo entrenado con datos sintéticos: no reemplaza las alertas por umbral ni la "
        "decisión del técnico (ver models/riesgo/tarjeta_modelo_v1.md)."
    )

    @classmethod
    def de(cls, r: EvaluacionRiesgoModelo) -> RiesgoModeloSalida:
        return cls(
            estanque_id=r.estanque.id,
            estanque=r.estanque.nombre,
            nivel=r.nivel,
            probabilidad=r.probabilidad,
            factores=[FactorSalida(nombre=f.nombre, aporte=f.aporte) for f in r.factores],
            version_modelo=r.version_modelo,
            puntos=r.puntos,
            basada_en_hasta=r.basada_en_hasta,
            mensaje=r.mensaje,
        )


@router.get("/estanques/{estanque_id}/riesgo-modelo", response_model=RiesgoModeloSalida)
def riesgo_modelo(
    estanque_id: int,
    usuario: Usuario = Depends(usuario_actual),
    c: Contenedor = Depends(contenedor),
) -> RiesgoModeloSalida:
    """Probabilidad de que el estanque llegue a condición crítica (OD o temperatura) en las
    próximas 6 h, estimada por el modelo entrenado sobre las 24 h previas a la última lectura."""
    return RiesgoModeloSalida.de(c.riesgo_modelo.evaluar(estanque_id, usuario))
