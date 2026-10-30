"""Router de lecturas de calidad de agua y estado del panel (RF-03)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from src.adapters.inbound.rest.dependencias import Contenedor, contenedor, usuario_actual
from src.adapters.inbound.rest.errores import RESPUESTAS_ERROR
from src.adapters.inbound.rest.esquemas import (
    AlertaSalida,
    EstadoEstanque,
    EvaluacionSalida,
    LecturaEntrada,
    LecturaRegistradaSalida,
    LecturaSalida,
    PuntoTendencia,
    RiesgoSalida,
)
from src.domain.model.usuario import Usuario
from src.ports.inbound.registrar_lectura import ComandoRegistrarLectura

router = APIRouter(prefix="/api", tags=["lecturas"], responses=RESPUESTAS_ERROR)


@router.post("/lecturas", response_model=LecturaRegistradaSalida, status_code=201)
def registrar_lectura(
    datos: LecturaEntrada,
    usuario: Usuario = Depends(usuario_actual),
    c: Contenedor = Depends(contenedor),
) -> LecturaRegistradaSalida:
    """Registra una lectura (formulario o sensor simulado). Valores físicamente imposibles
    (pH fuera de 0–14, OD < 0, temperatura fuera de 0–40 °C) se rechazan con 422.

    La lectura se evalúa contra config/umbrales.yaml y, si un parámetro está en
    PRECAUCIÓN o CRÍTICA, se crea una alerta (sin duplicar una abierta del mismo
    estanque, parámetro y nivel)."""
    resultado = c.lecturas.registrar(
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
    return LecturaRegistradaSalida(
        **LecturaSalida.de(resultado.lectura).model_dump(),
        evaluacion=[EvaluacionSalida.de(e) for e in resultado.evaluaciones],
        alertas=[AlertaSalida.de(a) for a in resultado.alertas_nuevas],
    )


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
    request: Request,
    puntos: int = Query(20, ge=0, le=200, description="Lecturas para la tendencia"),
    usuario: Usuario = Depends(usuario_actual),
    c: Contenedor = Depends(contenedor),
) -> list[EstadoEstanque]:
    """Estado de todos los estanques activos; el panel web lo consulta cada 1 s."""
    sim = getattr(request.app.state, "simulador", None)
    resultado = []
    for e in c.estanques.listar(usuario):
        estado = c.lecturas.estado(e.id, usuario)
        recientes = c.lecturas.recientes(e.id, usuario, puntos) if puntos else []
        simulacion = sim.de(e.id) if sim else None
        pred = c.prediccion.predecir(e.id, usuario).principal
        con_aviso = pred is not None and pred.estado.value in ("RIESGO", "YA_CRITICO")
        resultado.append(
            EstadoEstanque(
                estanque_id=e.id,
                nombre=e.nombre,
                ultima_lectura=LecturaSalida.de(estado.lectura) if estado.lectura else None,
                niveles=estado.niveles,
                alertas_abiertas=[AlertaSalida.de(a) for a in estado.alertas_abiertas],
                riesgo=RiesgoSalida.de(c.historial.riesgo(e.id, usuario)),
                tendencia=[PuntoTendencia.de(x) for x in reversed(recientes)],
                simulacion=simulacion.escenario if simulacion else None,
                prediccion=pred.mensaje if con_aviso else None,
                prediccion_estado=pred.estado.value if pred else None,
            )
        )
    return resultado
