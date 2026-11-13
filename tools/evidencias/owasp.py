"""Evidencias OWASP Top 10:2025 ejecutadas contra TruchaSmart desplegado con docker compose.

Uso: docker compose up -d --build && python tools/evidencias/owasp.py a01   (a01, a02, a04, a05,
a07, a08, a09 o a10). A03 (cadena de suministro) se evidencia con Dependabot en GitHub.
"""

import subprocess
import sys
import time
from pathlib import Path

import httpx

sys.stdout.reconfigure(encoding="utf-8")
URL = "http://localhost:8000"
RAIZ = Path(__file__).resolve().parents[2]
api = httpx.Client(base_url=URL, timeout=15)


def token(usuario, clave):
    r = api.post("/api/auth/login", json={"nombre_usuario": usuario, "password": clave})
    return {"Authorization": f"Bearer {r.json()['access_token']}"} if r.status_code == 200 else {}


def ver(etiqueta, r, esperado):
    ok = "✓" if r.status_code == esperado else "✗"
    cuerpo = r.text[:110].replace("\n", " ")
    print(f"{ok} {etiqueta:<62} → {r.status_code} (esperado {esperado})  {cuerpo}")


def psql(sql):
    r = subprocess.run(["docker", "compose", "exec", "-T", "db", "psql", "-U", "trucha", "-d", "truchasmart", "-c", sql],
                       capture_output=True, text=True, encoding="utf-8", cwd=RAIZ)  # fmt: skip
    print(r.stdout.rstrip())


modo = sys.argv[1]
SUFIJO = time.strftime("%H%M%S")  # nombres únicos en cada ejecución
ADMIN, OPER = token("admin", "Admin123!"), token("operario", "Oper123!")

if modo == "a01":
    print("A01 Broken Access Control — permisos por rol verificados en el servidor\n")
    ver("Sin sesión: GET /api/estanques", api.get("/api/estanques"), 401)
    ver(
        "Token alterado: GET /api/estanques",
        api.get("/api/estanques", headers={"Authorization": "Bearer abc.def.ghi"}),
        401,
    )
    ver(
        "Operario crea un estanque: POST /api/estanques",
        api.post("/api/estanques", json={"nombre": "Intruso"}, headers=OPER),
        403,
    )
    ver("Operario lista usuarios: GET /api/usuarios", api.get("/api/usuarios", headers=OPER), 403)
    ver(
        "Operario consulta la bitácora: GET /api/auditoria",
        api.get("/api/auditoria", headers=OPER),
        403,
    )
    ver(
        "Administrador lista usuarios: GET /api/usuarios",
        api.get("/api/usuarios", headers=ADMIN),
        200,
    )
elif modo == "a02":
    print("A02 Security Misconfiguration — cabeceras HTTP y arranque seguro en producción\n")
    r = api.get("/login")
    for h in (
        "content-security-policy",
        "x-frame-options",
        "x-content-type-options",
        "referrer-policy",
        "permissions-policy",
    ):
        print(f"{'✓' if h in r.headers else '✗'} {h}: {r.headers.get(h, '(ausente)')[:110]}")
    print("\n$ docker run --rm -e APP_ENV=produccion trucha-smart-app   (sin JWT_SECRET propio)")
    d = subprocess.run(["docker", "run", "--rm", "-e", "APP_ENV=produccion", "trucha-smart-app"],
                       capture_output=True, text=True, encoding="utf-8", timeout=60)  # fmt: skip
    for linea in (d.stdout + d.stderr).splitlines():
        if "ConfiguracionInsegura" in linea or "Application startup failed" in linea:
            print("  " + linea.strip()[:150])
    print(f"  código de salida del contenedor: {d.returncode} (la app no arranca)")
    print("\n$ docker compose exec app whoami")
    w = subprocess.run(["docker", "compose", "exec", "-T", "app", "whoami"], capture_output=True, text=True,
                       cwd=RAIZ)  # fmt: skip
    print(f"  {w.stdout.strip()}   (el proceso no corre como root)")
elif modo == "a04":
    print("A04 Cryptographic Failures — contraseñas y claves guardadas solo como hash\n")
    r = api.post("/api/integraciones", json={"nombre": "Evidencia A04"}, headers=ADMIN)
    secreto = r.json()["clave"]
    print(
        f"Clave de integración emitida (se muestra una sola vez): {secreto[:8]}…  ({len(secreto)} caracteres)\n"
    )
    psql(
        "SELECT nombre_usuario, left(password_hash, 7) AS algoritmo_bcrypt, length(password_hash) AS largo FROM usuarios;"
    )
    psql(
        "SELECT nombre, prefijo, length(hash_clave) AS largo_sha256, hash_clave LIKE 'ts_%' AS guarda_secreto_en_claro FROM claves_integracion ORDER BY id DESC LIMIT 1;"
    )
elif modo == "a05":
    print("A05 Injection — entradas maliciosas tratadas como datos\n")
    ver(
        "Login con inyección SQL: ' OR '1'='1",
        api.post(
            "/api/auth/login",
            json={"nombre_usuario": "admin' OR '1'='1' --", "password": "x' OR '1'='1"},
        ),
        401,
    )
    ver(
        "Filtro con inyección: ?estado=ABIERTA' OR 1=1--",
        api.get("/api/alertas?estado=ABIERTA' OR 1=1--", headers=ADMIN),
        422,
    )
    pisc = token("piscicultor", "Pisci123!")
    r = api.post(
        "/api/estanques", json={"nombre": f"<script>alert({SUFIJO})</script>"}, headers=pisc
    )
    ver("Estanque con nombre <script>…</script>", r, 201)
    eid = r.json()["id"]
    web = httpx.Client(base_url=URL)
    web.post("/login", data={"nombre_usuario": "piscicultor", "password": "Pisci123!"})
    html = web.get(f"/estanques/{eid}").text
    print(f"{'✓' if '&lt;script&gt;' in html and '<script>alert(' not in html else '✗'} La página muestra el nombre escapado: "
          f"{f'&lt;script&gt;alert({SUFIJO})&lt;/script&gt;' if '&lt;script&gt;' in html else '(no escapado)'}")  # fmt: skip
    api.delete(f"/api/estanques/{eid}", headers=pisc)
elif modo == "a07":
    print("A07 Authentication Failures — bloqueo tras 3 intentos fallidos (HU-11)\n")
    api.post("/api/usuarios", json={"nombre_usuario": f"evidencia.{SUFIJO}", "nombre_completo": "Usuario Evidencia A07",
                                    "password": "Correcta123!", "rol": "OPERARIO"}, headers=ADMIN)  # fmt: skip
    for i in range(1, 4):
        ver(
            f"Intento {i} con contraseña incorrecta",
            api.post(
                "/api/auth/login",
                json={"nombre_usuario": f"evidencia.{SUFIJO}", "password": "Adivinada1"},
            ),
            401 if i < 3 else 423,
        )
    ver(
        "Contraseña correcta durante el bloqueo",
        api.post(
            "/api/auth/login",
            json={"nombre_usuario": f"evidencia.{SUFIJO}", "password": "Correcta123!"},
        ),
        423,
    )
elif modo == "a08":
    print(
        "A08 Software or Data Integrity Failures — API externa de solo lectura con clave revocable\n"
    )
    r = api.post("/api/integraciones", json={"nombre": "Evidencia A08"}, headers=ADMIN).json()
    clave = {"X-API-Key": r["clave"]}
    ver(
        "GET /api/externa/v1/estanques con clave activa",
        api.get("/api/externa/v1/estanques", headers=clave),
        200,
    )
    ver(
        "POST /api/externa/v1/estanques (escritura)",
        api.post("/api/externa/v1/estanques", json={}, headers=clave),
        405,
    )
    ver(
        "Revocar la clave: DELETE /api/integraciones/{id}",
        api.delete(f"/api/integraciones/{r['id']}", headers=ADMIN),
        200,
    )
    ver(
        "GET /api/externa/v1/estanques con la clave revocada",
        api.get("/api/externa/v1/estanques", headers=clave),
        401,
    )
    print(
        "\n$ docker image inspect trucha-smart-app  (imagen construida desde el Dockerfile del repositorio)"
    )
    d = subprocess.run(["docker", "image", "inspect", "trucha-smart-app", "--format", "{{.Id}}  creada {{.Created}}  usuario={{.Config.User}}"],
                       capture_output=True, text=True)  # fmt: skip
    print("  " + d.stdout.strip())
elif modo == "a09":
    print("A09 Security Logging and Alerting Failures — bitácora de seguridad sin secretos\n")
    r = api.get("/api/auditoria?limite=12", headers=ADMIN).json()
    for e in r:
        print(
            f"  {e['momento'][:19]}  {e['tipo']:<24} usuario={str(e['nombre_usuario']):<16} ip={e['ip']:<12} {e['detalle'][:45]}"
        )
    texto = str(r)
    print(
        f"\n{'✓' if 'Adivinada1' not in texto and 'Correcta123!' not in texto else '✗'} Ninguna contraseña aparece en la bitácora"
    )
elif modo == "a10":
    print("A10 Mishandling of Exceptional Conditions — errores controlados, sin trazas internas\n")
    for etiqueta, r, esp in [
        ("Estanque inexistente: GET /api/estanques/999", api.get("/api/estanques/999", headers=ADMIN), 404),
        ("JSON inválido: POST /api/lecturas", api.post("/api/lecturas", content=b"{no es json", headers={**ADMIN, "Content-Type": "application/json"}), 422),
        ("pH imposible (15): POST /api/lecturas", api.post("/api/lecturas", json={"estanque_id": 1, "temperatura_c": 12, "oxigeno_mg_l": 8, "ph": 15}, headers=ADMIN), 422),
        ("Salud del servicio: GET /api/salud", api.get("/api/salud"), 200),
    ]:  # fmt: skip
        ver(etiqueta, r, esp)
        if "Traceback" in r.text or 'File "' in r.text:
            print("  ✗ la respuesta expone una traza interna")
