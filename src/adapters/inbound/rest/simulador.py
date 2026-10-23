"""Router para controlar el sensor simulado desde la web (demostraciones, ADR-004)."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, FastAPI, Request, Response
from pydantic import BaseModel, Field

from src.adapters.inbound.rest.dependencias import (
    Contenedor,
    contenedor,
    usuario_actual,
)
from src.adapters.inbound.rest.errores import RESPUESTAS_ERROR
from src.adapters.inbound.simulator.en_proceso import (
    ErrorSimulacion,
    EstadoSimulacion,
    SimuladorEnProceso,
)
from src.adapters.inbound.simulator.escenarios import Medicion
from src.domain.errores import Conflicto, ErrorValidacion, NoEncontrado
from src.domain.model.lectura_agua import FuenteLectura
from src.domain.model.usuario import Permiso, Usuario
from src.ports.inbound.registrar_lectura import ComandoRegistrarLectura

router = APIRouter(prefix="/api/simulador", tags=["simulador"], responses=RESPUESTAS_ERROR)


class SimulacionEntrada(BaseModel):
    estanque_id: int
    escenario: str = Field(
        default="normal", examples=["normal", "critico_oxigeno", "critico_temperatura"]
    )
    intervalo_s: float = Field(default=3.0, description="Entre 1 y 60 segundos")


class SimulacionSalida(BaseModel):
    estanque_id: int
    escenario: str
    intervalo_s: float
    iniciada_en: datetime
    lecturas_enviadas: int
    ultimo_error: str | None

    @classmethod
    def de(cls, s: EstadoSimulacion) -> SimulacionSalida:
        return cls(
            estanque_id=s.estanque_id,
            escenario=s.escenario,
            intervalo_s=s.intervalo_s,
            iniciada_en=s.iniciada_en,
            lecturas_enviadas=s.lecturas_enviadas,
            ultimo_error=s.ultimo_error,
        )


def crear_simulador(app: FastAPI) -> SimuladorEnProceso:
    """El paso del simulador abre su propia sesión y usa el caso de uso registrar_lectura."""

    def ejecutar_paso(estanque_id: int, usuario_id: int, m: Medicion) -> None:
        recursos = app.state.recursos
        sesion = recursos.bd.sesion()
        try:
            c = Contenedor(sesion, recursos)
            usuario = c.usuarios.usuario_activo(usuario_id)
            if usuario is None:
                raise NoEncontrado("El usuario que inició la simulación ya no está activo")
            c.lecturas.registrar(
                ComandoRegistrarLectura(
                    estanque_id=estanque_id,
                    temperatura_c=m.temperatura_c,
                    oxigeno_mg_l=m.oxigeno_mg_l,
                    ph=m.ph,
                    fuente=FuenteLectura.SENSOR,
                ),
                usuario,
            )
            c.confirmar()
        except Exception:
            sesion.rollback()
            raise
        finally:
            sesion.close()

    return SimuladorEnProceso(ejecutar_paso)


def simulador(request: Request) -> SimuladorEnProceso:
    return request.app.state.simulador


@router.get("", response_model=list[SimulacionSalida])
def simulaciones_activas(
    usuario: Usuario = Depends(usuario_actual),
    sim: SimuladorEnProceso = Depends(simulador),
) -> list[SimulacionSalida]:
    usuario.exigir(Permiso.CONSULTAR)
    return [SimulacionSalida.de(s) for s in sim.activas()]


@router.post("", response_model=SimulacionSalida, status_code=201)
def iniciar_simulacion(
    datos: SimulacionEntrada,
    usuario: Usuario = Depends(usuario_actual),
    c: Contenedor = Depends(contenedor),
    sim: SimuladorEnProceso = Depends(simulador),
) -> SimulacionSalida:
    """Inicia (o reinicia) el sensor simulado de un estanque. Piscicultor o Administrador."""
    usuario.exigir(Permiso.GESTIONAR_ESTANQUES)
    estanque = c.estanques.obtener(datos.estanque_id, usuario)
    if not estanque.activo:
        raise Conflicto(f"El estanque {estanque.nombre} está dado de baja")
    try:
        estado = sim.iniciar(estanque.id, datos.escenario, datos.intervalo_s, usuario.id)
    except ErrorSimulacion as e:
        raise ErrorValidacion(
            "escenario" if "Escenario" in str(e) else "intervalo_s", str(e)
        ) from e
    return SimulacionSalida.de(estado)


@router.delete("/{estanque_id}", status_code=204)
def detener_simulacion(
    estanque_id: int,
    usuario: Usuario = Depends(usuario_actual),
    sim: SimuladorEnProceso = Depends(simulador),
) -> Response:
    usuario.exigir(Permiso.GESTIONAR_ESTANQUES)
    if not sim.detener(estanque_id):
        raise NoEncontrado(f"No hay una simulación activa en el estanque {estanque_id}")
    return Response(status_code=204)
