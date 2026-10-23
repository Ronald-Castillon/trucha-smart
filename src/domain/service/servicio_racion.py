"""Caso de uso recomendar_racion: biomasa del lote + última lectura del estanque (RF-07)."""

from __future__ import annotations

from src.domain.errores import Conflicto, NoEncontrado
from src.domain.model.lectura_agua import Parametro
from src.domain.model.usuario import Permiso, Usuario
from src.domain.service.calculadora_fcr import biomasa_kg, peces_vivos
from src.domain.service.evaluador_calidad_agua import EvaluadorCalidadAgua
from src.domain.service.recomendador_racion import RecomendadorRacion
from src.ports.inbound.recomendar_racion import RecomendacionLote
from src.ports.outbound.repositorio_lectura import RepositorioLectura
from src.ports.outbound.repositorio_lote import RepositorioLote
from src.ports.outbound.repositorio_mortalidad import RepositorioMortalidad


class ServicioRacion:
    """Implementa el puerto de entrada RecomendarRacion."""

    def __init__(
        self,
        lotes: RepositorioLote,
        mortalidad: RepositorioMortalidad,
        lecturas: RepositorioLectura,
        evaluador: EvaluadorCalidadAgua,
        recomendador: RecomendadorRacion,
    ) -> None:
        self._lotes = lotes
        self._mortalidad = mortalidad
        self._lecturas = lecturas
        self._evaluador = evaluador
        self._recomendador = recomendador

    def recomendar(self, lote_id: int, solicitante: Usuario) -> RecomendacionLote:
        solicitante.exigir(Permiso.CONSULTAR)
        lote = self._lotes.por_id(lote_id)
        if lote is None:
            raise NoEncontrado(f"No existe el lote {lote_id}")
        if not lote.activo:
            raise Conflicto(f"El lote {lote.codigo} está cerrado")
        vivos = peces_vivos(lote, self._mortalidad.total(lote_id))
        lectura = self._lecturas.ultima_de(lote.estanque_id)
        niveles = self._evaluador.niveles(lectura) if lectura else {}
        recomendacion = self._recomendador.recomendar(
            biomasa_kg=biomasa_kg(vivos, lote.peso_medio_actual_g),
            peso_medio_g=lote.peso_medio_actual_g,
            nivel_temperatura=niveles.get(Parametro.TEMPERATURA),
            nivel_oxigeno=niveles.get(Parametro.OXIGENO_DISUELTO),
        )
        return RecomendacionLote(lote, vivos, lectura, recomendacion)
