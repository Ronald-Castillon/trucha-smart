"""Caso de uso gestionar_estanque: estanques/jaulas y lotes (RF-02)."""

from __future__ import annotations

from datetime import date

from src.domain.errores import Conflicto, NoEncontrado
from src.domain.model.estanque import Estanque
from src.domain.model.lote import Lote
from src.domain.model.usuario import Permiso, Usuario
from src.ports.inbound.gestionar_estanque import ComandoSembrarLote, DatosEstanque
from src.ports.outbound.reloj import Reloj
from src.ports.outbound.repositorio_estanque import RepositorioEstanque
from src.ports.outbound.repositorio_lote import RepositorioLote


class ServicioEstanques:
    """Implementa el puerto de entrada GestionarEstanque."""

    def __init__(
        self, estanques: RepositorioEstanque, lotes: RepositorioLote, reloj: Reloj
    ) -> None:
        self._estanques = estanques
        self._lotes = lotes
        self._reloj = reloj

    # -- estanques ---------------------------------------------------------
    def crear(self, datos: DatosEstanque, solicitante: Usuario) -> Estanque:
        solicitante.exigir(Permiso.GESTIONAR_ESTANQUES)
        estanque = Estanque(
            nombre=datos.nombre,
            tipo=datos.tipo,
            volumen_m3=datos.volumen_m3,
            ubicacion=datos.ubicacion,
            creado_en=self._reloj.ahora(),
        )
        self._exigir_nombre_libre(estanque.nombre)
        return self._estanques.guardar(estanque)

    def actualizar(self, estanque_id: int, datos: DatosEstanque, solicitante: Usuario) -> Estanque:
        solicitante.exigir(Permiso.GESTIONAR_ESTANQUES)
        actual = self._estanque(estanque_id)
        nuevo = Estanque(
            nombre=datos.nombre,
            tipo=datos.tipo,
            volumen_m3=datos.volumen_m3,
            ubicacion=datos.ubicacion,
            creado_en=actual.creado_en,
            activo=actual.activo,
            id=actual.id,
        )
        if nuevo.nombre != actual.nombre:
            self._exigir_nombre_libre(nuevo.nombre)
        return self._estanques.guardar(nuevo)

    def desactivar(self, estanque_id: int, solicitante: Usuario) -> None:
        solicitante.exigir(Permiso.GESTIONAR_ESTANQUES)
        estanque = self._estanque(estanque_id)
        if self._lotes.activo_de(estanque_id) is not None:
            raise Conflicto("No se puede dar de baja un estanque con un lote activo")
        estanque.activo = False
        self._estanques.guardar(estanque)

    def obtener(self, estanque_id: int, solicitante: Usuario) -> Estanque:
        solicitante.exigir(Permiso.CONSULTAR)
        return self._estanque(estanque_id)

    def listar(self, solicitante: Usuario) -> list[Estanque]:
        solicitante.exigir(Permiso.CONSULTAR)
        return self._estanques.listar(solo_activos=True)

    # -- lotes -------------------------------------------------------------
    def sembrar_lote(self, comando: ComandoSembrarLote, solicitante: Usuario) -> Lote:
        solicitante.exigir(Permiso.GESTIONAR_ESTANQUES)
        estanque = self._estanque(comando.estanque_id)
        lote = Lote.sembrar(
            estanque_id=estanque.id,
            codigo=comando.codigo,
            num_peces=comando.num_peces,
            peso_medio_g=comando.peso_medio_g,
            fecha_siembra=comando.fecha_siembra,
            hoy=self._reloj.ahora().date(),
        )
        if not estanque.activo:
            raise Conflicto(f"El estanque {estanque.nombre} está dado de baja")
        existente = self._lotes.activo_de(estanque.id)
        if existente is not None:
            raise Conflicto(
                f"El estanque {estanque.nombre} ya tiene el lote activo {existente.codigo}; "
                "ciérrelo antes de sembrar otro"
            )
        if self._lotes.por_codigo(lote.codigo) is not None:
            raise Conflicto(f"Ya existe un lote con el código {lote.codigo}")
        return self._lotes.guardar(lote)

    def lote_activo(self, estanque_id: int, solicitante: Usuario) -> Lote | None:
        solicitante.exigir(Permiso.CONSULTAR)
        self._estanque(estanque_id)
        return self._lotes.activo_de(estanque_id)

    def lotes_de(self, estanque_id: int, solicitante: Usuario) -> list[Lote]:
        solicitante.exigir(Permiso.CONSULTAR)
        self._estanque(estanque_id)
        return self._lotes.de_estanque(estanque_id)

    def obtener_lote(self, lote_id: int, solicitante: Usuario) -> Lote:
        solicitante.exigir(Permiso.CONSULTAR)
        return self._lote(lote_id)

    def actualizar_peso(self, lote_id: int, peso_medio_g: float, solicitante: Usuario) -> Lote:
        solicitante.exigir(Permiso.GESTIONAR_ESTANQUES)
        lote = self._lote(lote_id)
        lote.actualizar_peso(peso_medio_g)
        return self._lotes.guardar(lote)

    def cerrar_lote(self, lote_id: int, fecha: date, solicitante: Usuario) -> Lote:
        solicitante.exigir(Permiso.GESTIONAR_ESTANQUES)
        lote = self._lote(lote_id)
        lote.cerrar(fecha)
        return self._lotes.guardar(lote)

    # -- auxiliares --------------------------------------------------------
    def _estanque(self, estanque_id: int) -> Estanque:
        estanque = self._estanques.por_id(estanque_id)
        if estanque is None:
            raise NoEncontrado(f"No existe el estanque {estanque_id}")
        return estanque

    def _lote(self, lote_id: int) -> Lote:
        lote = self._lotes.por_id(lote_id)
        if lote is None:
            raise NoEncontrado(f"No existe el lote {lote_id}")
        return lote

    def _exigir_nombre_libre(self, nombre: str) -> None:
        if self._estanques.por_nombre(nombre) is not None:
            raise Conflicto(f"Ya existe un estanque llamado '{nombre}'")
