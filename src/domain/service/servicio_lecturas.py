"""Caso de uso registrar_lectura (RF-03)."""

from __future__ import annotations

from datetime import timedelta

from src.domain.errores import Conflicto, ErrorValidacion, NoEncontrado
from src.domain.model.lectura_agua import LecturaAgua
from src.domain.model.usuario import Permiso, Usuario
from src.ports.inbound.registrar_lectura import ComandoRegistrarLectura
from src.ports.outbound.reloj import Reloj
from src.ports.outbound.repositorio_estanque import RepositorioEstanque
from src.ports.outbound.repositorio_lectura import RepositorioLectura

# Tolerancia para relojes de sensores ligeramente adelantados.
TOLERANCIA_FUTURO = timedelta(minutes=5)
LIMITE_MAXIMO_CONSULTA = 500


class ServicioLecturas:
    """Implementa el puerto de entrada RegistrarLectura."""

    def __init__(
        self, lecturas: RepositorioLectura, estanques: RepositorioEstanque, reloj: Reloj
    ) -> None:
        self._lecturas = lecturas
        self._estanques = estanques
        self._reloj = reloj

    def registrar(self, comando: ComandoRegistrarLectura, solicitante: Usuario) -> LecturaAgua:
        solicitante.exigir(Permiso.REGISTRAR_LECTURA)
        self._estanque_activo(comando.estanque_id)
        ahora = self._reloj.ahora()
        medido_en = comando.medido_en or ahora
        if medido_en.tzinfo is None:
            raise ErrorValidacion("medido_en", "La fecha de medición debe incluir zona horaria")
        if medido_en > ahora + TOLERANCIA_FUTURO:
            raise ErrorValidacion("medido_en", "La fecha de medición no puede ser futura")
        lectura = LecturaAgua(
            estanque_id=comando.estanque_id,
            temperatura_c=comando.temperatura_c,
            oxigeno_mg_l=comando.oxigeno_mg_l,
            ph=comando.ph,
            fuente=comando.fuente,
            medido_en=medido_en,
            registrado_por=solicitante.id,
        )
        return self._lecturas.guardar(lectura)

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
