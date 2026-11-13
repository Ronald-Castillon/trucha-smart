# Prueba de carga (RNF-P) — resultado medido

Generado por `tools/prueba_carga.py` el 2026-11-07T01:52:55+00:00 con Locust (Windows 11, 20 núcleos, 31.8 GB, BD postgresql+psycopg, 4 workers uvicorn). Locust y la API se ejecutan en la misma máquina y comparten CPU.

Carga: **500 usuarios concurrentes** (rampa 25.0/s) durante 120 s; escenario tests/carga/locustfile.py (90 % consulta, 10 % sensores).

| Métrica | Valor medido | Meta (guía S10) | ¿Cumple? |
|---|---:|---:|:---:|
| Latencia p95 | 1700 ms | < 800 ms | No |
| Tasa de errores | 0.219 % | < 1.0 % | Sí |
| Throughput | 179.8 RPS | — | — |
| Latencia p50 / p99 | 270 / 2100 ms | — | — |
| Memoria del servidor (promedio / máx.) | 481.1 / 500.2 MB | — | — |
| CPU del servidor (máx., suma de workers) | 932.1 % | — | — |

Peticiones: 21499 (47 fallidas).

Por fase (muestras crudas de cada petición; la rampa incluye el inicio de sesión de
los usuarios, que usa bcrypt y es intensivo en CPU por diseño):

| Fase | Duración | Peticiones | p50 ms | p95 ms | p99 ms | Errores | RPS | p95 < meta |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| rampa | 20.0 s | 3096 | 62 | 494 | 686 | 0.0 % | 154.9 | Sí |
| estable | 99.5 s | 18427 | 324 | 1725 | 2182 | 0.255 % | 185.3 | No |

| Endpoint | Peticiones | Fallos | p50 ms | p95 ms | p99 ms | RPS |
|---|---:|---:|---:|---:|---:|---:|
| `GET /api/alertas` | 3995 | 10 | 140 | 1400 | 1800 | 33.4 |
| `GET /api/estanques/{id}/historial` | 1894 | 5 | 160 | 1400 | 1900 | 15.8 |
| `GET /api/estanques/{id}/prediccion` | 2012 | 1 | 160 | 1400 | 2000 | 16.8 |
| `GET /api/panel` | 11695 | 27 | 380 | 1800 | 2300 | 97.8 |
| `POST /api/lecturas` | 1403 | 4 | 220 | 1400 | 1900 | 11.7 |
| `login` | 500 | 0 | 390 | 660 | 820 | 4.2 |

Errores registrados por Locust (los más frecuentes):

- `GET /api/panel` × 27: HTTPError('500 Server Error: Internal Server Error for url: GET /api/panel')
- `GET /api/alertas` × 10: HTTPError('500 Server Error: Internal Server Error for url: GET /api/alertas')
- `GET /api/estanques/{id}/historial` × 5: HTTPError('500 Server Error: Internal Server Error for url: GET /api/estanques/{id}/historial')
- `POST /api/lecturas` × 2: HTTPError('500 Server Error: Internal Server Error for url: POST /api/lecturas')
- `POST /api/lecturas` × 2: ConnectionResetError(10054, 'Se ha forzado la interrupción de una conexión existente por el host remoto', None, 10054, None)
- `GET /api/estanques/{id}/prediccion` × 1: HTTPError('500 Server Error: Internal Server Error for url: GET /api/estanques/{id}/prediccion')
