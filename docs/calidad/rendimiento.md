# Prueba de carga (RNF-P) — resultado medido

Generado por `tools/prueba_carga.py` el 2026-10-30T04:31:19+00:00 con Locust (Windows 11, 20 núcleos, 31.8 GB, BD sqlite, 8 workers uvicorn). Locust y la API se ejecutan en la misma máquina y comparten CPU.

Carga: **500 usuarios concurrentes** (rampa 25.0/s) durante 120 s; escenario tests/carga/locustfile.py (90 % consulta, 10 % sensores).

| Métrica | Valor medido | Meta (guía S10) | ¿Cumple? |
|---|---:|---:|:---:|
| Latencia p95 | 390 ms | < 800 ms | Sí |
| Tasa de errores | 0.016 % | < 1.0 % | Sí |
| Throughput | 206.3 RPS | — | — |
| Latencia p50 / p99 | 18 / 1800 ms | — | — |
| Memoria del servidor (promedio / máx.) | 827.6 / 897.9 MB | — | — |
| CPU del servidor (máx., suma de workers) | 1505.0 % | — | — |

Peticiones: 24633 (4 fallidas).

Por fase (muestras crudas de cada petición; la rampa incluye el inicio de sesión de
los usuarios, que usa bcrypt y es intensivo en CPU por diseño):

| Fase | Duración | Peticiones | p50 ms | p95 ms | p99 ms | Errores | RPS | p95 < meta |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| rampa | 20.0 s | 3239 | 14 | 367 | 599 | 0.031 % | 162.0 | Sí |
| estable | 99.7 s | 21473 | 19 | 438 | 1936 | 0.014 % | 215.4 | Sí |

| Endpoint | Peticiones | Fallos | p50 ms | p95 ms | p99 ms | RPS |
|---|---:|---:|---:|---:|---:|---:|
| `GET /api/alertas` | 4475 | 0 | 6 | 21 | 74 | 37.5 |
| `GET /api/estanques/{id}/historial` | 2222 | 0 | 9 | 60 | 150 | 18.6 |
| `GET /api/estanques/{id}/prediccion` | 2342 | 0 | 11 | 220 | 680 | 19.6 |
| `GET /api/panel` | 13587 | 0 | 26 | 770 | 2200 | 113.8 |
| `POST /api/lecturas` | 1507 | 4 | 8 | 35 | 120 | 12.6 |
| `login` | 500 | 0 | 320 | 470 | 700 | 4.2 |

Errores registrados por Locust (los más frecuentes):

- `POST /api/lecturas` × 2: RemoteDisconnected('Remote end closed connection without response')
- `POST /api/lecturas` × 2: ConnectionResetError(10054, 'Se ha forzado la interrupci�n de una conexi�n existente por el host remoto', None, 10054, None)
