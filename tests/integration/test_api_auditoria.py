"""RF-11 por la API REST y la web: 423 tras 3 fallos y bitácora para el Administrador."""


def _login(cliente, password, usuario="operario"):
    return cliente.post("/api/auth/login", json={"nombre_usuario": usuario, "password": password})


def test_cp_rf11_01_api_responde_423_y_desbloquea_a_los_5_minutos(cliente, reloj):
    assert [_login(cliente, "mala").status_code for _ in range(3)] == [401, 401, 423]
    r = _login(cliente, "Oper123!")
    assert r.status_code == 423 and r.json()["error"] == "cuenta_bloqueada"
    assert "5 min" in r.json()["detalle"]
    reloj.avanzar(minutes=5)
    assert _login(cliente, "Oper123!").status_code == 200


def test_login_web_muestra_el_bloqueo(cliente):
    for _ in range(3):
        r = cliente.post("/login", data={"nombre_usuario": "operario", "password": "mala"})
    assert r.status_code == 423 and "Cuenta bloqueada" in r.text


def test_cp_rf11_02_bitacora_registra_accesos_y_claves(cliente, como_admin, como_operario):
    _login(cliente, "mala")
    cliente.get("/api/externa/v1/estanques", headers={"X-API-Key": "ts_falsa"})
    clave = cliente.post("/api/integraciones", json={"nombre": "ERP"}, headers=como_admin).json()
    cliente.delete(f"/api/integraciones/{clave['id']}", headers=como_admin)
    eventos = cliente.get("/api/auditoria", headers=como_admin).json()
    tipos = [e["tipo"] for e in eventos]
    for esperado in ("CLAVE_REVOCADA", "CLAVE_CREADA", "CLAVE_RECHAZADA", "LOGIN_FALLIDO"):
        assert esperado in tipos
    assert tipos.count("LOGIN_EXITOSO") >= 2  # los inicios de sesión de los fixtures
    assert all(e["momento"] and e["ip"] for e in eventos)
    texto = str(eventos)
    assert "mala" not in texto and "ts_falsa" not in texto and clave["clave"] not in texto
    assert cliente.get("/api/auditoria", headers=como_operario).status_code == 403
    cliente.post("/login", data={"nombre_usuario": "admin", "password": "Admin123!"})
    html = cliente.get("/auditoria").text
    assert "Bitácora de seguridad" in html and "Clave de integración revocada" in html
