"""RNF-+: cabeceras de seguridad HTTP y configuración segura para producción (OWASP A02)."""

import pytest

from src.adapters.config import Configuracion, ConfiguracionInsegura
from src.main import crear_recursos


def test_cabeceras_de_seguridad_en_web_y_api(cliente, como_operario):
    web = cliente.get("/login")
    assert web.headers["X-Frame-Options"] == "DENY"
    assert web.headers["X-Content-Type-Options"] == "nosniff"
    assert web.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    csp = web.headers["Content-Security-Policy"]
    assert "default-src 'self'" in csp and "frame-ancestors 'none'" in csp
    api = cliente.get("/api/panel", headers=como_operario)
    assert api.headers["Cache-Control"] == "no-store" and "Content-Security-Policy" in api.headers
    assert "Content-Security-Policy" not in cliente.get("/docs").headers  # Swagger usa CDN


def test_produccion_rechaza_la_clave_jwt_de_ejemplo_o_corta(tmp_path):
    url = f"sqlite:///{(tmp_path / 'p.db').as_posix()}"
    for secreto in (Configuracion.jwt_secret, "corta-de-20-caracter"):
        with pytest.raises(ConfiguracionInsegura, match="JWT_SECRET"):
            crear_recursos(
                Configuracion(database_url=url, jwt_secret=secreto, entorno="produccion")
            )
    ok = crear_recursos(Configuracion(database_url=url, jwt_secret="x" * 48, entorno="produccion"))
    assert ok.cookie_segura is True
    assert crear_recursos(Configuracion(database_url=url)).cookie_segura is False  # desarrollo
