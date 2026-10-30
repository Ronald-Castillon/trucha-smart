"""Caso de uso consultar_auditoria y registro de eventos de seguridad (RF-11, OWASP A09)."""

from __future__ import annotations

from src.domain.model.evento_seguridad import EventoSeguridad, TipoEvento
from src.domain.model.usuario import Permiso, Usuario
from src.ports.outbound.reloj import Reloj
from src.ports.outbound.repositorio_evento_seguridad import RepositorioEventoSeguridad

MAXIMO_EVENTOS = 1000


class ServicioAuditoria:
    """Implementa ConsultarAuditoria; los demás servicios lo usan para registrar eventos."""

    def __init__(self, eventos: RepositorioEventoSeguridad, reloj: Reloj) -> None:
        self._eventos = eventos
        self._reloj = reloj

    def registrar(
        self,
        tipo: TipoEvento,
        nombre_usuario: str | None = None,
        usuario_id: int | None = None,
        ip: str | None = None,
        detalle: str = "",
    ) -> EventoSeguridad:
        nombre = nombre_usuario[:50] if nombre_usuario else None
        return self._eventos.guardar(
            EventoSeguridad(tipo, self._reloj.ahora(), nombre, usuario_id, ip, detalle[:200])
        )

    def listar(self, solicitante: Usuario, limite: int = 200) -> list[EventoSeguridad]:
        solicitante.exigir(Permiso.GESTIONAR_USUARIOS)
        return self._eventos.recientes(max(1, min(limite, MAXIMO_EVENTOS)))
