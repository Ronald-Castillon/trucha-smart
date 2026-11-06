# Prueba de carga (RNF-P) — resultado medido

Generado por `tools/prueba_carga.py` el 2026-11-06T03:23:56+00:00 con Locust (Linux 7.0.0-1019-azure, 4 núcleos, 15.6 GB, BD postgresql+psycopg, 4 workers uvicorn). Locust y la API se ejecutan en la misma máquina y comparten CPU.

Carga: **500 usuarios concurrentes** (rampa 25.0/s) durante 120 s; escenario tests/carga/locustfile.py (90 % consulta, 10 % sensores).

| Métrica | Valor medido | Meta (guía S10) | ¿Cumple? |
|---|---:|---:|:---:|
| Latencia p95 | 34000 ms | < 800 ms | No |
| Tasa de errores | 1.88 % | < 1.0 % | No |
| Throughput | 57.5 RPS | — | — |
| Latencia p50 / p99 | 45 / 73000 ms | — | — |
| Memoria del servidor (promedio / máx.) | 499.1 / 512.4 MB | — | — |
| CPU del servidor (máx., suma de workers) | 391.5 % | — | — |

Peticiones: 6860 (129 fallidas).

Por fase (muestras crudas de cada petición; la rampa incluye el inicio de sesión de
los usuarios, que usa bcrypt y es intensivo en CPU por diseño):

| Fase | Duración | Peticiones | p50 ms | p95 ms | p99 ms | Errores | RPS | p95 < meta |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| rampa | 19.5 s | 379 | 5840 | 14872 | 16944 | 2.111 % | 19.4 | No |
| estable | 98.3 s | 6507 | 42 | 34584 | 73043 | 1.875 % | 66.2 | No |

| Endpoint | Peticiones | Fallos | p50 ms | p95 ms | p99 ms | RPS |
|---|---:|---:|---:|---:|---:|---:|
| `GET /api/alertas` | 1133 | 15 | 10 | 6900 | 59000 | 9.5 |
| `GET /api/estanques/{id}/historial` | 587 | 10 | 15 | 6000 | 61000 | 4.9 |
| `GET /api/estanques/{id}/prediccion` | 586 | 13 | 17 | 13000 | 59000 | 4.9 |
| `GET /api/panel` | 3570 | 53 | 64 | 8700 | 61000 | 29.9 |
| `POST /api/lecturas` | 484 | 8 | 19 | 31000 | 63000 | 4.1 |
| `login` | 500 | 30 | 13000 | 92000 | 95000 | 4.2 |

Errores registrados por Locust (los más frecuentes):

- `GET /api/panel` × 48: HTTPError('500 Server Error: Internal Server Error for url: GET /api/panel')
- `login` × 30: HTTPError('500 Server Error: Internal Server Error for url: login')
- `GET /api/alertas` × 15: HTTPError('500 Server Error: Internal Server Error for url: GET /api/alertas')
- `GET /api/estanques/{id}/prediccion` × 11: HTTPError('500 Server Error: Internal Server Error for url: GET /api/estanques/{id}/prediccion')
- `GET /api/estanques/{id}/historial` × 8: HTTPError('500 Server Error: Internal Server Error for url: GET /api/estanques/{id}/historial')
- `POST /api/lecturas` × 5: HTTPError('500 Server Error: Internal Server Error for url: POST /api/lecturas')
- `GET /api/panel` × 4: RemoteDisconnected('Remote end closed connection without response')
- `POST /api/lecturas` × 3: RemoteDisconnected('Remote end closed connection without response')
- `GET /api/estanques/{id}/historial` × 2: RemoteDisconnected('Remote end closed connection without response')
- `GET /api/estanques/{id}/prediccion` × 1: RemoteDisconnected('Remote end closed connection without response')
