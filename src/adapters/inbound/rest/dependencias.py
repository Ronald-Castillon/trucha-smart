"""Inyección de dependencias: recursos de la app, contenedor por petición y usuario actual."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from functools import cached_property

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.adapters.outbound.persistence.db import BaseDatos
from src.adapters.outbound.persistence.repositorio_alerta_sql import RepositorioAlertaSQL
from src.adapters.outbound.persistence.repositorio_estanque_sql import (
    RepositorioEstanqueSQL,
    RepositorioLoteSQL,
)
from src.adapters.outbound.persistence.repositorio_lectura_sql import RepositorioLecturaSQL
from src.adapters.outbound.persistence.repositorio_usuario_sql import RepositorioUsuarioSQL
from src.adapters.outbound.security.jwt_tokens import ServicioTokens
from src.domain.model.umbral import ConjuntoUmbrales
from src.domain.model.usuario import Usuario
from src.domain.service.evaluador_calidad_agua import EvaluadorCalidadAgua
from src.domain.service.servicio_alertas import ServicioAlertas
from src.domain.service.servicio_estanques import ServicioEstanques
from src.domain.service.servicio_lecturas import ServicioLecturas
from src.domain.service.servicio_usuarios import ServicioUsuarios
from src.ports.outbound.hasher_password import HasherPassword
from src.ports.outbound.notificador import Notificador
from src.ports.outbound.reloj import Reloj

COOKIE_SESION = "ts_token"


class NoAutenticado(Exception):
    """No hay sesión válida (HTTP 401 en API, redirección a /login en web)."""


@dataclass
class Recursos:
    """Objetos de vida larga creados una vez en la raíz de composición."""

    bd: BaseDatos
    hasher: HasherPassword
    tokens: ServicioTokens
    reloj: Reloj
    umbrales: ConjuntoUmbrales
    notificador: Notificador


class Contenedor:
    """Construye los casos de uso para una petición, sobre una única sesión de BD."""

    def __init__(self, sesion: Session, recursos: Recursos) -> None:
        self.sesion = sesion
        self.recursos = recursos

    def confirmar(self) -> None:
        self.sesion.commit()

    @cached_property
    def usuarios(self) -> ServicioUsuarios:
        r = self.recursos
        return ServicioUsuarios(RepositorioUsuarioSQL(self.sesion), r.hasher, r.reloj)

    @cached_property
    def repo_estanques(self) -> RepositorioEstanqueSQL:
        return RepositorioEstanqueSQL(self.sesion)

    @cached_property
    def repo_lotes(self) -> RepositorioLoteSQL:
        return RepositorioLoteSQL(self.sesion)

    @cached_property
    def estanques(self) -> ServicioEstanques:
        return ServicioEstanques(self.repo_estanques, self.repo_lotes, self.recursos.reloj)

    @cached_property
    def repo_lecturas(self) -> RepositorioLecturaSQL:
        return RepositorioLecturaSQL(self.sesion)

    @cached_property
    def lecturas(self) -> ServicioLecturas:
        r = self.recursos
        return ServicioLecturas(
            self.repo_lecturas,
            self.repo_estanques,
            self.repo_alertas,
            EvaluadorCalidadAgua(r.umbrales),
            r.notificador,
            r.reloj,
        )

    @cached_property
    def repo_alertas(self) -> RepositorioAlertaSQL:
        return RepositorioAlertaSQL(self.sesion)

    @cached_property
    def alertas(self) -> ServicioAlertas:
        return ServicioAlertas(self.repo_alertas, self.recursos.reloj)


def recursos(request: Request) -> Recursos:
    return request.app.state.recursos


def contenedor(request: Request) -> Iterator[Contenedor]:
    r: Recursos = request.app.state.recursos
    sesion = r.bd.sesion()
    try:
        yield Contenedor(sesion, r)
    except Exception:
        sesion.rollback()
        raise
    finally:
        sesion.close()


_bearer = HTTPBearer(auto_error=False, description="Token JWT obtenido en /api/auth/login")


def usuario_actual(
    request: Request,
    credenciales: HTTPAuthorizationCredentials | None = Depends(_bearer),
    c: Contenedor = Depends(contenedor),
) -> Usuario:
    token = credenciales.credentials if credenciales else request.cookies.get(COOKIE_SESION)
    usuario_id = c.recursos.tokens.usuario_id(token) if token else None
    usuario = c.usuarios.usuario_activo(usuario_id) if usuario_id is not None else None
    if usuario is None:
        raise NoAutenticado()
    return usuario
