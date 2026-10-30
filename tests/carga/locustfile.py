"""RNF-P: escenario de carga con Locust (equivalente a un script k6 / plan JMeter).

Perfil de uso de la piscigranja: la mayoría de usuarios consulta el panel en vivo (como hace
panel.js), revisa alertas, historial y predicción; una parte simula sensores que registran lecturas.
Lo ejecuta tools/prueba_carga.py (o: locust -f tests/carga/locustfile.py --host http://...).
"""

import csv
import os
import random
import time

from locust import HttpUser, between, events, task

_muestras: list[tuple[float, float, str, int]] = []


@events.request.add_listener
def _registrar(request_type, name, response_time, exception, **_):
    """Guarda cada petición (instante, ms, endpoint, ok) para calcular percentiles por fase."""
    _muestras.append((time.time(), response_time, name, 0 if exception else 1))


@events.quitting.add_listener
def _volcar(environment, **_):
    destino = os.environ.get("LOCUST_MUESTRAS")
    if destino:
        with open(destino, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(_muestras)


USUARIOS = [("piscicultor", "Pisci123!"), ("operario", "Oper123!"), ("admin", "Admin123!")]
ESTANQUES = [1, 2, 3]


class Consulta(HttpUser):
    """Piscicultor u operario con el panel abierto (lectura intensiva)."""

    weight = 9
    wait_time = between(1, 3)

    def on_start(self):
        nombre, password = random.choice(USUARIOS)
        r = self.client.post(
            "/api/auth/login", json={"nombre_usuario": nombre, "password": password}, name="login"
        )
        self.client.headers["Authorization"] = f"Bearer {r.json()['access_token']}"

    @task(6)
    def panel(self):
        self.client.get("/api/panel", name="GET /api/panel")

    @task(2)
    def alertas(self):
        self.client.get("/api/alertas", name="GET /api/alertas")

    @task(1)
    def historial(self):
        e = random.choice(ESTANQUES)
        self.client.get(
            f"/api/estanques/{e}/historial?desde=2026-10-16&hasta=2026-10-22",
            name="GET /api/estanques/{id}/historial",
        )

    @task(1)
    def prediccion(self):
        e = random.choice(ESTANQUES)
        self.client.get(f"/api/estanques/{e}/prediccion", name="GET /api/estanques/{id}/prediccion")


class Sensor(HttpUser):
    """Sensor (vía operario) que envía una lectura cada pocos segundos (escritura)."""

    weight = 1
    wait_time = between(2, 5)

    def on_start(self):
        r = self.client.post(
            "/api/auth/login",
            json={"nombre_usuario": "operario", "password": "Oper123!"},
            name="login",
        )
        self.client.headers["Authorization"] = f"Bearer {r.json()['access_token']}"

    @task
    def registrar(self):
        self.client.post(
            "/api/lecturas",
            json={
                "estanque_id": random.choice(ESTANQUES),
                "temperatura_c": round(random.uniform(11, 14), 1),
                "oxigeno_mg_l": round(random.uniform(7, 9), 1),
                "ph": round(random.uniform(7, 7.8), 1),
            },
            name="POST /api/lecturas",
        )
