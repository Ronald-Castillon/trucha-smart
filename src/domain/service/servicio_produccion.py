"""Caso de uso registrar_alimentacion: alimento, mortalidad, biomasa y FCR (RF-06)."""

from __future__ import annotations

from datetime import datetime, timedelta

from src.domain.errores import Conflicto, ErrorValidacion, NoEncontrado
from src.domain.model.lote import Lote
from src.domain.model.registro_alimentacion import RegistroAlimentacion
from src.domain.model.registro_mortalidad import RegistroMortalidad
from src.domain.model.usuario import Permiso, Usuario
from src.domain.service.calculadora_fcr import ResumenProduccion, resumen_produccion
from src.ports.outbound.reloj import Reloj
from src.ports.outbound.repositorio_alimentacion import RepositorioAlimentacion
from src.ports.outbound.repositorio_lote import RepositorioLote
from src.ports.outbound.repositorio_mortalidad import RepositorioMortalidad

TOLERANCIA_FUTURO = timedelta(minutes=5)


class ServicioProduccion:
    """Implementa el puerto de entrada RegistrarAlimentacion."""

    def __init__(
        self,
        lotes: RepositorioLote,
        alimentacion: RepositorioAlimentacion,
        mortalidad: RepositorioMortalidad,
        reloj: Reloj,
    ) -> None:
        self._lotes = lotes
        self._alimentacion = alimentacion
        self._mortalidad = mortalidad
        self._reloj = reloj

    def registrar_alimentacion(
        self,
        lote_id: int,
        cantidad_kg: float,
        solicitante: Usuario,
        registrado_en: datetime | None = None,
    ) -> RegistroAlimentacion:
        solicitante.exigir(Permiso.REGISTRAR_ALIMENTACION)
        self._lote_activo(lote_id)
        registro = RegistroAlimentacion(
            lote_id=lote_id,
            cantidad_kg=cantidad_kg,
            registrado_en=self._momento(registrado_en),
            registrado_por=solicitante.id,
        )
        return self._alimentacion.guardar(registro)

    def registrar_mortalidad(
        self,
        lote_id: int,
        cantidad: int,
        causa: str | None,
        solicitante: Usuario,
        registrado_en: datetime | None = None,
    ) -> RegistroMortalidad:
        solicitante.exigir(Permiso.REGISTRAR_ALIMENTACION)
        lote = self._lote_activo(lote_id)
        registro = RegistroMortalidad(
            lote_id=lote_id,
            cantidad=cantidad,
            causa=causa,
            registrado_en=self._momento(registrado_en),
            registrado_por=solicitante.id,
        )
        vivos = lote.num_peces_inicial - self._mortalidad.total(lote_id)
        if cantidad > vivos:
            raise ErrorValidacion(
                "cantidad", f"La mortalidad ({cantidad}) supera los peces vivos del lote ({vivos})"
            )
        return self._mortalidad.guardar(registro)

    def produccion(self, lote_id: int, solicitante: Usuario) -> ResumenProduccion:
        solicitante.exigir(Permiso.CONSULTAR)
        lote = self._lote(lote_id)
        return resumen_produccion(
            lote, self._mortalidad.total(lote_id), self._alimentacion.total_kg(lote_id)
        )

    def alimentaciones(self, lote_id: int, solicitante: Usuario) -> list[RegistroAlimentacion]:
        solicitante.exigir(Permiso.CONSULTAR)
        self._lote(lote_id)
        return self._alimentacion.de_lote(lote_id)

    def mortalidades(self, lote_id: int, solicitante: Usuario) -> list[RegistroMortalidad]:
        solicitante.exigir(Permiso.CONSULTAR)
        self._lote(lote_id)
        return self._mortalidad.de_lote(lote_id)

    def _momento(self, registrado_en: datetime | None) -> datetime:
        ahora = self._reloj.ahora()
        momento = registrado_en or ahora
        if momento.tzinfo is None:
            raise ErrorValidacion("registrado_en", "La fecha debe incluir zona horaria")
        if momento > ahora + TOLERANCIA_FUTURO:
            raise ErrorValidacion("registrado_en", "La fecha no puede ser futura")
        return momento

    def _lote(self, lote_id: int) -> Lote:
        lote = self._lotes.por_id(lote_id)
        if lote is None:
            raise NoEncontrado(f"No existe el lote {lote_id}")
        return lote

    def _lote_activo(self, lote_id: int) -> Lote:
        lote = self._lote(lote_id)
        if not lote.activo:
            raise Conflicto(f"El lote {lote.codigo} está cerrado")
        return lote
