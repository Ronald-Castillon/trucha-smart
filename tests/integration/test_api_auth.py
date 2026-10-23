"""RF-01 por la API REST y la web sobre SQLite."""

from fastapi.testclient import TestClient

NUEVO = {
    "nombre_usuario": "juan",
    "nombre_completo": "Juan Pérez",
    "password": "Secreta123",
    "rol": "OPERARIO",
}


def test_cp_rf01_01_login_api_devuelve_jwt(cliente: TestClient):
    """CP-RF01-01: login correcto devuelve un JWT Bearer utilizable."""
    r = cliente.post("/api/auth/login", json={"nombre_usuario": "operario", "password": "Oper123!"})
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["token_type"] == "bearer" and cuerpo["usuario"]["rol"] == "OPERARIO"
    yo = cliente.get("/api/auth/yo", headers={"Authorization": f"Bearer {cuerpo['access_token']}"})
    assert yo.status_code == 200 and yo.json()["nombre_usuario"] == "operario"


def test_cp_rf01_01_login_web_fija_cookie_httponly(cliente: TestClient):
    """CP-RF01-01: login web deja la sesión en cookie HttpOnly y redirige al panel."""
    r = cliente.post(
        "/login",
        data={"nombre_usuario": "operario", "password": "Oper123!"},
        follow_redirects=False,
    )
    assert r.status_code == 303 and r.headers["location"] == "/panel"
    assert "httponly" in r.headers["set-cookie"].lower()
    panel = cliente.get("/panel")
    assert panel.status_code == 200 and "Usuario Operario" in panel.text


def test_cp_rf01_02_login_invalido_da_401_con_mensaje(cliente: TestClient):
    """CP-RF01-02: credenciales inválidas -> 401 con mensaje claro y sin token."""
    for datos in (
        {"nombre_usuario": "operario", "password": "incorrecta"},
        {"nombre_usuario": "fantasma", "password": "Oper123!"},
    ):
        r = cliente.post("/api/auth/login", json=datos)
        assert r.status_code == 401
        assert r.json() == {
            "error": "credenciales_invalidas",
            "detalle": "Usuario o contraseña incorrectos",
            "campo": None,
        }
    web = cliente.post("/login", data={"nombre_usuario": "operario", "password": "x"})
    assert web.status_code == 401 and "Usuario o contraseña incorrectos" in web.text
    assert "set-cookie" not in web.headers


def test_sin_token_o_token_invalido_da_401(cliente: TestClient):
    assert cliente.get("/api/auth/yo").status_code == 401
    r = cliente.get("/api/auth/yo", headers={"Authorization": "Bearer basura"})
    assert r.status_code == 401 and r.json()["error"] == "no_autenticado"


def test_web_sin_sesion_redirige_a_login(cliente: TestClient):
    r = cliente.get("/panel", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/login"


def test_logout_elimina_la_cookie(cliente: TestClient):
    cliente.post("/login", data={"nombre_usuario": "operario", "password": "Oper123!"})
    r = cliente.post("/logout", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/login"
    assert cliente.get("/panel", follow_redirects=False).status_code == 303
    assert cliente.post("/api/auth/logout").status_code == 204


def test_admin_registra_y_lista_usuarios(cliente: TestClient, como_admin):
    r = cliente.post("/api/usuarios", json=NUEVO, headers=como_admin)
    assert r.status_code == 201 and r.json()["rol"] == "OPERARIO"
    assert "password" not in r.json() and "password_hash" not in r.json()
    nombres = [u["nombre_usuario"] for u in cliente.get("/api/usuarios", headers=como_admin).json()]
    assert "juan" in nombres
    login = {"nombre_usuario": "juan", "password": "Secreta123"}
    assert cliente.post("/api/auth/login", json=login).status_code == 200
    assert cliente.post("/api/usuarios", json=NUEVO, headers=como_admin).status_code == 409


def test_operario_y_piscicultor_no_gestionan_usuarios(cliente, como_operario, como_piscicultor):
    for enc in (como_operario, como_piscicultor):
        r = cliente.post("/api/usuarios", json=NUEVO, headers=enc)
        assert r.status_code == 403 and r.json()["error"] == "permiso_denegado"


def test_validacion_de_esquema_tiene_formato_consistente(cliente, como_admin):
    r = cliente.post("/api/usuarios", json={"nombre_usuario": "x"}, headers=como_admin)
    assert r.status_code == 422
    assert r.json()["error"] == "validacion" and r.json()["campo"]


def test_password_corta_da_422_con_campo(cliente, como_admin):
    r = cliente.post("/api/usuarios", json={**NUEVO, "password": "corta"}, headers=como_admin)
    assert r.status_code == 422 and r.json()["campo"] == "password"


def test_web_usuarios_operario_ve_error_403(cliente):
    cliente.post("/login", data={"nombre_usuario": "operario", "password": "Oper123!"})
    r = cliente.get("/usuarios")
    assert r.status_code == 403 and "no tiene permiso" in r.text


def test_web_admin_registra_usuario_por_formulario(cliente):
    cliente.post("/login", data={"nombre_usuario": "admin", "password": "Admin123!"})
    r = cliente.post("/usuarios", data=NUEVO)
    assert r.status_code == 200 and "registrado" in r.text and "juan" in r.text
    r = cliente.post("/usuarios", data=NUEVO)
    assert r.status_code == 422 and "ya está registrado" in r.text
