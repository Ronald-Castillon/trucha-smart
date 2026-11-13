"""Consume la API REST pública de TruchaSmart desplegada en Render (login JWT + endpoints)."""

import json
import urllib.request

URL = "https://truchasmart.onrender.com"


def pedir(ruta, datos=None, token=None):
    cab = {"Content-Type": "application/json"}
    if token:
        cab["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(
        URL + ruta, data=json.dumps(datos).encode() if datos else None, headers=cab
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.status, json.loads(r.read())


st, s = pedir("/api/auth/login", {"nombre_usuario": "piscicultor", "password": "Pisci123!"})
print(
    f"POST /api/auth/login -> {st}  usuario={s['usuario']['nombre_usuario']} rol={s['usuario']['rol']} token={s['access_token'][:20]}..."
)
tk = s["access_token"]
st, panel = pedir("/api/panel", token=tk)
items = panel if isinstance(panel, list) else panel.get("estanques", panel)
print(
    f"GET /api/panel -> {st}  estanques: {[e.get('nombre', e) for e in items] if isinstance(items, list) else list(items)[:5]}"
)
st, r = pedir("/api/estanques/3/riesgo-modelo", token=tk)
print(f"GET /api/estanques/3/riesgo-modelo -> {st}")
print(json.dumps(r, ensure_ascii=False, indent=1)[:900])
