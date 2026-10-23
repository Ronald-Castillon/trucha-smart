"""Fixtures compartidas: app FastAPI sobre SQLite en memoria y usuarios de cada rol."""

from __future__ import annotations

import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from src.adapters.config import RAIZ, cargar_umbrales
from src.adapters.inbound.rest.dependencias import Recursos
from src.adapters.outbound.notification.notificador_log import NotificadorLog
from src.adapters.outbound.persistence.db import Base, BaseDatos
from src.adapters.outbound.persistence.repositorio_usuario_sql import RepositorioUsuarioSQL
from src.adapters.outbound.security.bcrypt_hasher import HasherBcrypt
from src.adapters.outbound.security.jwt_tokens import ServicioTokens
from src.domain.model.usuario import Rol, Usuario
from src.main import crear_app
from tests.fakes import RelojFijo

PASSWORDS = {
    Rol.ADMINISTRADOR: "Admin123!",
    Rol.PISCICULTOR: "Pisci123!",
    Rol.OPERARIO: "Oper123!",
}
NOMBRES = {Rol.ADMINISTRADOR: "admin", Rol.PISCICULTOR: "piscicultor", Rol.OPERARIO: "operario"}


@pytest.fixture
def reloj() -> RelojFijo:
    return RelojFijo()


# TEST_DATABASE_URL permite correr las pruebas de integración contra PostgreSQL (CI, ADR-003).
URL_PRUEBAS = os.getenv("TEST_DATABASE_URL", "sqlite://")


@pytest.fixture
def recursos(reloj) -> Iterator[Recursos]:
    bd = BaseDatos(URL_PRUEBAS)
    Base.metadata.drop_all(bd.motor)
    bd.crear_tablas()
    hasher = HasherBcrypt(rondas=4)
    with bd.sesion() as s:
        repo = RepositorioUsuarioSQL(s)
        for rol in Rol:
            repo.guardar(
                Usuario(
                    nombre_usuario=NOMBRES[rol],
                    nombre_completo=f"Usuario {rol.value.title()}",
                    password_hash=hasher.hashear(PASSWORDS[rol]),
                    rol=rol,
                    creado_en=reloj.ahora(),
                )
            )
        s.commit()
    yield Recursos(
        bd=bd,
        hasher=hasher,
        tokens=ServicioTokens("clave-de-pruebas-de-32-bytes-o-mas!", 60),
        reloj=reloj,
        umbrales=cargar_umbrales(RAIZ / "config" / "umbrales.yaml"),
        notificador=NotificadorLog(),
    )
    Base.metadata.drop_all(bd.motor)
    bd.motor.dispose()


@pytest.fixture
def cliente(recursos) -> TestClient:
    with TestClient(crear_app(recursos=recursos)) as c:
        yield c


def encabezado(cliente: TestClient, rol: Rol) -> dict[str, str]:
    r = cliente.post(
        "/api/auth/login", json={"nombre_usuario": NOMBRES[rol], "password": PASSWORDS[rol]}
    )
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def como_admin(cliente) -> dict[str, str]:
    return encabezado(cliente, Rol.ADMINISTRADOR)


@pytest.fixture
def como_piscicultor(cliente) -> dict[str, str]:
    return encabezado(cliente, Rol.PISCICULTOR)


@pytest.fixture
def como_operario(cliente) -> dict[str, str]:
    return encabezado(cliente, Rol.OPERARIO)
