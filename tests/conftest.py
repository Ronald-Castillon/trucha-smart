"""Fixtures compartidas: app FastAPI sobre SQLite en memoria y usuarios de cada rol."""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from src.adapters.inbound.rest.dependencias import Recursos
from src.adapters.outbound.persistence.db import BaseDatos
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


@pytest.fixture
def recursos(reloj) -> Iterator[Recursos]:
    bd = BaseDatos("sqlite://")
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
    )
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
