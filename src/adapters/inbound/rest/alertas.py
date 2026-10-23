"""Router de alertas y su atención (RF-04)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from src.adapters.inbound.rest.dependencias import Contenedor, contenedor, usuario_actual
from src.adapters.inbound.rest.errores import RESPUESTAS_ERROR
from src.adapters.inbound.rest.esquemas import AlertaSalida, AtencionEntrada
from src.domain.model.alerta import EstadoAlerta
from src.domain.model.usuario import Usuario

router = APIRouter(prefix="/api", tags=["alertas"], responses=RESPUESTAS_ERROR)


@router.get("/alertas", response_model=list[AlertaSalida])
def listar_alertas(
    estado: EstadoAlerta | None = None,
    estanque_id: int | None = None,
    limite: int = Query(100, ge=1, le=500),
    usuario: Usuario = Depends(usuario_actual),
    c: Contenedor = Depends(contenedor),
) -> list[AlertaSalida]:
    """Alertas de la más reciente a la más antigua; filtra por estado y estanque."""
    return [AlertaSalida.de(a) for a in c.alertas.listar(usuario, estanque_id, estado, limite)]


@router.post("/alertas/{alerta_id}/atender", response_model=AlertaSalida)
def atender_alerta(
    alerta_id: int,
    datos: AtencionEntrada | None = None,
    usuario: Usuario = Depends(usuario_actual),
    c: Contenedor = Depends(contenedor),
) -> AlertaSalida:
    """Marca la alerta como ATENDIDA registrando el usuario y la fecha/hora (B-06).
    Una alerta ya atendida devuelve 409."""
    alerta = c.alertas.atender(alerta_id, datos.observacion if datos else None, usuario)
    c.confirmar()
    return AlertaSalida.de(alerta)
