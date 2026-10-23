"""Caso de uso atender_alerta (RF-04)."""

from __future__ import annotations

from src.domain.errores import NoEncontrado
from src.domain.model.alerta import Alerta, EstadoAlerta
from src.domain.model.usuario import Permiso, Usuario
from src.ports.outbound.reloj import Reloj
from src.ports.outbound.repositorio_alerta import RepositorioAlerta


class ServicioAlertas:
    """Implementa el puerto de entrada AtenderAlerta."""

    def __init__(self, alertas: RepositorioAlerta, reloj: Reloj) -> None:
        self._alertas = alertas
        self._reloj = reloj

    def atender(self, alerta_id: int, observacion: str | None, solicitante: Usuario) -> Alerta:
        solicitante.exigir(Permiso.ATENDER_ALERTA)
        alerta = self._alertas.por_id(alerta_id)
        if alerta is None:
            raise NoEncontrado(f"No existe la alerta {alerta_id}")
        alerta.atender(solicitante.id, self._reloj.ahora(), observacion)
        return self._alertas.guardar(alerta)

    def listar(
        self,
        solicitante: Usuario,
        estanque_id: int | None = None,
        estado: EstadoAlerta | None = None,
        limite: int = 100,
    ) -> list[Alerta]:
        solicitante.exigir(Permiso.CONSULTAR)
        return self._alertas.listar(estanque_id, estado, max(1, min(limite, 500)))
