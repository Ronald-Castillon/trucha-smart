"""Router de recomendación de ración diaria (RF-07)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from src.adapters.inbound.rest.dependencias import Contenedor, contenedor, usuario_actual
from src.adapters.inbound.rest.errores import RESPUESTAS_ERROR
from src.adapters.inbound.rest.esquemas import RacionSalida
from src.domain.model.usuario import Usuario

router = APIRouter(prefix="/api/lotes", tags=["ración"], responses=RESPUESTAS_ERROR)


@router.get("/{lote_id}/racion", response_model=RacionSalida)
def recomendar_racion(
    lote_id: int, usuario: Usuario = Depends(usuario_actual), c: Contenedor = Depends(contenedor)
) -> RacionSalida:
    """Ración diaria = biomasa × tasa(% según peso medio) × factor temperatura × factor oxígeno,
    con la regla aplicada. Con temperatura u oxígeno CRÍTICOS la ración es 0 (suspender)."""
    return RacionSalida.de(c.racion.recomendar(lote_id, usuario))
