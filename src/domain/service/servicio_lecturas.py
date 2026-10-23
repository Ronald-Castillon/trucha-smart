"""Caso de uso registrar_lectura: guarda la lectura, la evalúa y genera alertas (RF-03, RF-04)."""

from __future__ import annotations

from datetime import timedelta

from src.domain.errores import Conflicto, ErrorValidacion, NoEncontrado
from src.domain.model.alerta import Alerta, EstadoAlerta
from src.domain.model.lectura_agua import LecturaAgua
from src.domain.model.usuario import Permiso, Usuario
from src.domain.service.evaluador_calidad_agua import EvaluadorCalidadAgua
from src.ports.inbound.registrar_lectura import (
    ComandoRegistrarLectura,
    EstadoCalidad,
    ResultadoRegistroLectura,
)
from src.ports.outbound.notificador import Notificador
from src.ports.outbound.reloj import Reloj
from src.ports.outbound.repositorio_alerta import RepositorioAlerta
from src.ports.outbound.repositorio_estanque import RepositorioEstanque
from src.ports.outbound.repositorio_lectura import RepositorioLectura

# Tolerancia para relojes de sensores ligeramente adelantados.
TOLERANCIA_FUTURO = timedelta(minutes=5)
LIMITE_MAXIMO_CONSULTA = 500


class ServicioLecturas:
    """Implementa el puerto de entrada RegistrarLectura."""

    def __init__(
        self,
        lecturas: RepositorioLectura,
        estanques: RepositorioEstanque,
        alertas: RepositorioAlerta,
        evaluador: EvaluadorCalidadAgua,
        notificador: Notificador,
        reloj: Reloj,
    ) -> None:
        self._lecturas = lecturas
        self._estanques = estanques
        self._alertas = alertas
        self._evaluador = evaluador
        self._notificador = notificador
        self._reloj = reloj

    def registrar(
        self, comando: ComandoRegistrarLectura, solicitante: Usuario
    ) -> ResultadoRegistroLectura:
        solicitante.exigir(Permiso.REGISTRAR_LECTURA)
        self._estanque_activo(comando.estanque_id)
        ahora = self._reloj.ahora()
        medido_en = comando.medido_en or ahora
        if medido_en.tzinfo is None:
            raise ErrorValidacion("medido_en", "La fecha de medición debe incluir zona horaria")
        if medido_en > ahora + TOLERANCIA_FUTURO:
            raise ErrorValidacion("medido_en", "La fecha de medición no puede ser futura")
        lectura = self._lecturas.guardar(
            LecturaAgua(
                estanque_id=comando.estanque_id,
                temperatura_c=comando.temperatura_c,
                oxigeno_mg_l=comando.oxigeno_mg_l,
                ph=comando.ph,
                fuente=comando.fuente,
                medido_en=medido_en,
                registrado_por=solicitante.id,
            )
        )
        evaluaciones = self._evaluador.evaluar(lectura)
        nuevas = []
        for ev in evaluaciones:
            if not ev.requiere_alerta:
                continue
            # No duplicar: una sola alerta abierta por estanque, parámetro y nivel.
            if self._alertas.abierta(lectura.estanque_id, ev.parametro, ev.nivel) is not None:
                continue
            alerta = self._alertas.guardar(
                Alerta(
                    estanque_id=lectura.estanque_id,
                    lectura_id=lectura.id,
                    parametro=ev.parametro,
                    nivel=ev.nivel,
                    valor=ev.valor,
                    mensaje=ev.mensaje,
                    creada_en=ahora,
                )
            )
            nuevas.append(alerta)
        for alerta in nuevas:
            self._notificador.notificar(alerta)
        return ResultadoRegistroLectura(lectura, evaluaciones, nuevas)

    def ultima(self, estanque_id: int, solicitante: Usuario) -> LecturaAgua | None:
        solicitante.exigir(Permiso.CONSULTAR)
        self._estanque(estanque_id)
        return self._lecturas.ultima_de(estanque_id)

    def recientes(
        self, estanque_id: int, solicitante: Usuario, limite: int = 20
    ) -> list[LecturaAgua]:
        solicitante.exigir(Permiso.CONSULTAR)
        self._estanque(estanque_id)
        limite = max(1, min(limite, LIMITE_MAXIMO_CONSULTA))
        return self._lecturas.de_estanque(estanque_id, limite=limite)

    def estado(self, estanque_id: int, solicitante: Usuario) -> EstadoCalidad:
        ultima = self.ultima(estanque_id, solicitante)
        return EstadoCalidad(
            lectura=ultima,
            niveles=self._evaluador.niveles(ultima) if ultima else {},
            alertas_abiertas=self._alertas.listar(estanque_id, EstadoAlerta.ABIERTA),
        )

    def _estanque(self, estanque_id: int):
        estanque = self._estanques.por_id(estanque_id)
        if estanque is None:
            raise NoEncontrado(f"No existe el estanque {estanque_id}")
        return estanque

    def _estanque_activo(self, estanque_id: int):
        estanque = self._estanque(estanque_id)
        if not estanque.activo:
            raise Conflicto(f"El estanque {estanque.nombre} está dado de baja")
        return estanque
