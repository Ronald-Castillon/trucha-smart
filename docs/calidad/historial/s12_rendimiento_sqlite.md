# Prueba de carga (RNF-P) — resultado medido

Generado por `tools/prueba_carga.py` el 2026-11-06T20:23:28+00:00 con Locust (Windows 11, 20 núcleos, 31.8 GB, BD sqlite, 8 workers uvicorn). Locust y la API se ejecutan en la misma máquina y comparten CPU.

Carga: **500 usuarios concurrentes** (rampa 25.0/s) durante 120 s; escenario tests/carga/locustfile.py (90 % consulta, 10 % sensores).

| Métrica | Valor medido | Meta (guía S10) | ¿Cumple? |
|---|---:|---:|:---:|
| Latencia p95 | 660 ms | < 800 ms | Sí |
| Tasa de errores | 0.0 % | < 1.0 % | Sí |
| Throughput | 188.8 RPS | — | — |
| Latencia p50 / p99 | 26 / 1900 ms | — | — |
| Memoria del servidor (promedio / máx.) | 834.7 / 897.4 MB | — | — |
| CPU del servidor (máx., suma de workers) | 1386.0 % | — | — |

Peticiones: 22558 (0 fallidas).

Por fase (muestras crudas de cada petición; la rampa incluye el inicio de sesión de
los usuarios, que usa bcrypt y es intensivo en CPU por diseño):

| Fase | Duración | Peticiones | p50 ms | p95 ms | p99 ms | Errores | RPS | p95 < meta |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| rampa | 20.0 s | 3367 | 19 | 464 | 1210 | 0.0 % | 168.4 | Sí |
| estable | 98.6 s | 19266 | 28 | 721 | 2103 | 0.0 % | 195.3 | Sí |

| Endpoint | Peticiones | Fallos | p50 ms | p95 ms | p99 ms | RPS |
|---|---:|---:|---:|---:|---:|---:|
| `GET /api/alertas` | 4095 | 0 | 9 | 30 | 100 | 34.3 |
| `GET /api/estanques/{id}/historial` | 2110 | 0 | 12 | 80 | 190 | 17.7 |
| `GET /api/estanques/{id}/prediccion` | 2020 | 0 | 16 | 360 | 900 | 16.9 |
| `GET /api/panel` | 12392 | 0 | 41 | 990 | 2600 | 103.7 |
| `POST /api/lecturas` | 1445 | 0 | 13 | 64 | 180 | 12.1 |
| `login` | 496 | 0 | 360 | 1500 | 2200 | 4.2 |

Errores registrados por Locust (los más frecuentes):

