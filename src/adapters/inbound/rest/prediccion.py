"""Router de predicción de tendencia (RF-10)."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src.adapters.inbound.rest.dependencias import Contenedor, contenedor, usuario_actual
from src.adapters.inbound.rest.errores import RESPUESTAS_ERROR
from src.domain.model.lectura_agua import Parametro
from src.domain.model.usuario import Usuario
from src.domain.service.predictor_tendencia import EstadoPrediccion, Prediccion
from src.ports.inbound.predecir_tendencia import PrediccionEstanque

router = APIRouter(prefix="/api", tags=["predicción"], responses=RESPUESTAS_ERROR)


class PrediccionSalida(BaseModel):
    parametro: Parametro
    estado: EstadoPrediccion
    puntos: int
    valor_actual: float | None
    pendiente_por_hora: float | None
    r2: float | None
    limite: float | None
    horas_hasta_limite: float | None
    momento_estimado: datetime | None
    mensaje: str

    @classmethod
    def de(cls, p: Prediccion) -> PrediccionSalida:
        return cls(**{k: getattr(p, k) for k in cls.model_fields})


class PrediccionEstanqueSalida(BaseModel):
    estanque_id: int
    estanque: str
    basada_en_hasta: datetime | None
    principal: PrediccionSalida | None
    predicciones: list[PrediccionSalida]

    @classmethod
    def de(cls, p: PrediccionEstanque) -> PrediccionEstanqueSalida:
        return cls(
            estanque_id=p.estanque.id,
            estanque=p.estanque.nombre,
            basada_en_hasta=p.basada_en_hasta,
            principal=PrediccionSalida.de(p.principal) if p.principal else None,
            predicciones=[PrediccionSalida.de(x) for x in p.predicciones],
        )


@router.get("/estanques/{estanque_id}/prediccion", response_model=PrediccionEstanqueSalida)
def prediccion(
    estanque_id: int,
    usuario: Usuario = Depends(usuario_actual),
    c: Contenedor = Depends(contenedor),
) -> PrediccionEstanqueSalida:
    """Proyección lineal (mínimos cuadrados, 24 h previas a la última lectura) de cada
    parámetro y tiempo estimado hasta el límite crítico, si ocurre dentro de 6 h."""
    return PrediccionEstanqueSalida.de(c.prediccion.predecir(estanque_id, usuario))
