"""Caso de uso gestionar_integraciones: claves y API de solo lectura para terceros (RF-09)."""

from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta

from src.domain.errores import ClaveInvalida, ErrorValidacion, NoEncontrado
from src.domain.model.alerta import EstadoAlerta
from src.domain.model.clave_integracion import ClaveIntegracion, huella
from src.domain.model.evento_seguridad import TipoEvento
from src.domain.model.lectura_agua import LecturaAgua
from src.domain.model.usuario import Permiso, Usuario
from src.domain.service.evaluador_calidad_agua import EvaluadorCalidadAgua
from src.domain.service.servicio_auditoria import ServicioAuditoria
from src.ports.inbound.gestionar_integraciones import ClaveCreada, EstadoExterno
from src.ports.outbound.reloj import Reloj
from src.ports.outbound.repositorio_alerta import RepositorioAlerta
from src.ports.outbound.repositorio_clave_integracion import RepositorioClaveIntegracion
from src.ports.outbound.repositorio_estanque import RepositorioEstanque
from src.ports.outbound.repositorio_lectura import RepositorioLectura

DIAS_POR_DEFECTO = 7
MAXIMO_DIAS = 31
MAXIMO_LECTURAS = 2000


class ServicioIntegraciones:
    """Implementa el puerto de entrada GestionarIntegraciones."""

    def __init__(
        self,
        claves: RepositorioClaveIntegracion,
        estanques: RepositorioEstanque,
        lecturas: RepositorioLectura,
        alertas: RepositorioAlerta,
        evaluador: EvaluadorCalidadAgua,
        reloj: Reloj,
        auditoria: ServicioAuditoria | None = None,
    ) -> None:
        self._auditoria = auditoria
        self._claves = claves
        self._estanques = estanques
        self._lecturas = lecturas
        self._alertas = alertas
        self._evaluador = evaluador
        self._reloj = reloj

    # -- administración ----------------------------------------------------
    def crear(self, nombre: str, solicitante: Usuario, ip: str | None = None) -> ClaveCreada:
        solicitante.exigir(Permiso.GESTIONAR_USUARIOS)
        entidad, secreto = ClaveIntegracion.nueva(nombre, solicitante.id, self._reloj.ahora())
        guardada = self._claves.guardar(entidad)
        self._evento(
            TipoEvento.CLAVE_CREADA, solicitante, f"{guardada.nombre} ({guardada.prefijo}…)", ip
        )
        return ClaveCreada(guardada, secreto)

    def listar(self, solicitante: Usuario) -> list[ClaveIntegracion]:
        solicitante.exigir(Permiso.GESTIONAR_USUARIOS)
        return self._claves.listar()

    def revocar(
        self, clave_id: int, solicitante: Usuario, ip: str | None = None
    ) -> ClaveIntegracion:
        solicitante.exigir(Permiso.GESTIONAR_USUARIOS)
        clave = self._claves.por_id(clave_id)
        if clave is None:
            raise NoEncontrado(f"No existe la clave de integración {clave_id}")
        clave.revocar()
        self._evento(
            TipoEvento.CLAVE_REVOCADA, solicitante, f"{clave.nombre} ({clave.prefijo}…)", ip
        )
        return self._claves.guardar(clave)

    # -- consumo externo ---------------------------------------------------
    def autenticar(self, secreto: str | None, ip: str | None = None) -> ClaveIntegracion:
        """El rechazo se registra en la bitácora sin el valor de la clave (OWASP A09)."""
        clave = self._claves.por_hash(huella(secreto)) if secreto else None
        if clave is None or not clave.corresponde(secreto):
            if self._auditoria is not None:
                motivo = (
                    "cabecera X-API-Key ausente"
                    if not secreto
                    else "clave no reconocida o revocada"
                )
                self._auditoria.registrar(TipoEvento.CLAVE_RECHAZADA, ip=ip, detalle=motivo)
            raise ClaveInvalida()
        clave.ultimo_uso = self._reloj.ahora()
        return self._claves.guardar(clave)

    def _evento(self, tipo: TipoEvento, solicitante: Usuario, detalle: str, ip: str | None) -> None:
        if self._auditoria is not None:
            self._auditoria.registrar(tipo, solicitante.nombre_usuario, solicitante.id, ip, detalle)

    def estado_estanques(self, clave: ClaveIntegracion) -> list[EstadoExterno]:
        self._exigir_activa(clave)
        resultado = []
        for e in self._estanques.listar(solo_activos=True):
            ultima = self._lecturas.ultima_de(e.id)
            abiertas = self._alertas.listar(e.id, EstadoAlerta.ABIERTA)
            resultado.append(
                EstadoExterno(
                    estanque=e,
                    ultima_lectura=ultima,
                    niveles=self._evaluador.niveles(ultima) if ultima else {},
                    alertas_abiertas=len(abiertas),
                )
            )
        return resultado

    def lecturas(
        self, clave: ClaveIntegracion, estanque_id: int, desde: date | None, hasta: date | None
    ) -> list[LecturaAgua]:
        self._exigir_activa(clave)
        if self._estanques.por_id(estanque_id) is None:
            raise NoEncontrado(f"No existe el estanque {estanque_id}")
        hasta = hasta or self._reloj.ahora().date()
        desde = desde or hasta - timedelta(days=DIAS_POR_DEFECTO - 1)
        if desde > hasta:
            raise ErrorValidacion("desde", "La fecha 'desde' no puede ser posterior a 'hasta'")
        if (hasta - desde).days + 1 > MAXIMO_DIAS:
            raise ErrorValidacion(
                "desde", f"El rango máximo de la API externa es {MAXIMO_DIAS} días"
            )
        inicio = datetime.combine(desde, time.min, tzinfo=UTC)
        fin = datetime.combine(hasta, time.max, tzinfo=UTC)
        datos = self._lecturas.de_estanque(estanque_id, inicio, fin, MAXIMO_LECTURAS)
        return sorted(datos, key=lambda x: (x.medido_en, x.id or 0))

    @staticmethod
    def _exigir_activa(clave: ClaveIntegracion) -> None:
        if not clave.activa:
            raise ClaveInvalida()
