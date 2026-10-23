"""Router de lecturas de calidad de agua y estado del panel (RF-03)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from src.adapters.inbound.rest.dependencias import Contenedor, contenedor, usuario_actual
from src.adapters.inbound.rest.errores import RESPUESTAS_ERROR
from src.adapters.inbound.rest.esquemas import EstadoEstanque, LecturaEntrada, LecturaSalida
from src.domain.model.usuario import Usuario
from src.ports.inbound.registrar_lectura import ComandoRegistrarLectura

router = APIRouter(prefix="/api", tags=["lecturas"], responses=RESPUESTAS_ERROR)


@router.post("/lecturas", response_model=LecturaSalida, status_code=201)
def registrar_lectura(
    datos: LecturaEntrada,
    usuario: Usuario = Depends(usuario_actual),
    c: Contenedor = Depends(contenedor),
) -> LecturaSalida:
    """Registra una lectura (formulario o sensor simulado). Valores físicamente imposibles
    (pH fuera de 0–14, OD < 0, temperatura fuera de 0–40 °C) se rechazan con 422."""
    lectura = c.lecturas.registrar(
        ComandoRegistrarLectura(
            estanque_id=datos.estanque_id,
            temperatura_c=datos.temperatura_c,
            oxigeno_mg_l=datos.oxigeno_mg_l,
            ph=datos.ph,
            fuente=datos.fuente,
            medido_en=datos.medido_en,
        ),
        usuario,
    )
    c.confirmar()
    return LecturaSalida.de(lectura)


@router.get("/lecturas", response_model=list[LecturaSalida])
def lecturas_recientes(
    estanque_id: int,
    limite: int = Query(20, ge=1, le=500),
    usuario: Usuario = Depends(usuario_actual),
    c: Contenedor = Depends(contenedor),
) -> list[LecturaSalida]:
    """Lecturas más recientes de un estanque (la primera es la última registrada)."""
    return [LecturaSalida.de(x) for x in c.lecturas.recientes(estanque_id, usuario, limite)]


@router.get("/estanques/{estanque_id}/ultima-lectura", response_model=LecturaSalida | None)
def ultima_lectura(
    estanque_id: int,
    usuario: Usuario = Depends(usuario_actual),
    c: Contenedor = Depends(contenedor),
) -> LecturaSalida | None:
    lectura = c.lecturas.ultima(estanque_id, usuario)
    return LecturaSalida.de(lectura) if lectura else None


@router.get("/panel", response_model=list[EstadoEstanque], tags=["panel"])
def estado_panel(
    usuario: Usuario = Depends(usuario_actual), c: Contenedor = Depends(contenedor)
) -> list[EstadoEstanque]:
    """Estado de todos los estanques activos; el panel web lo consulta cada 2 s."""
    resultado = []
    for e in c.estanques.listar(usuario):
        ultima = c.lecturas.ultima(e.id, usuario)
        resultado.append(
            EstadoEstanque(
                estanque_id=e.id,
                nombre=e.nombre,
                ultima_lectura=LecturaSalida.de(ultima) if ultima else None,
            )
        )
    return resultado
