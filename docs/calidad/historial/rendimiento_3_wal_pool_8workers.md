# Prueba de carga (RNF-P) — resultado medido

Generado por `tools/prueba_carga.py` el 2026-10-30T04:27:16+00:00 con Locust (Windows 11, 20 núcleos, 31.8 GB, BD sqlite, 8 workers uvicorn). Locust y la API se ejecutan en la misma máquina y comparten CPU.

Carga: **500 usuarios concurrentes** (rampa 25.0/s) durante 120 s; escenario tests/carga/locustfile.py (90 % consulta, 10 % sensores).

| Métrica | Valor medido | Meta (guía S10) | ¿Cumple? |
|---|---:|---:|:---:|
| Latencia p95 | 1900 ms | < 800 ms | No |
| Tasa de errores | 0.013 % | < 1.0 % | Sí |
| Throughput | 195.2 RPS | — | — |
| Latencia p50 / p99 | 28 / 4100 ms | — | — |
| Memoria del servidor (promedio / máx.) | 841.0 / 881.7 MB | — | — |
| CPU del servidor (máx., suma de workers) | 1408.8 % | — | — |

Peticiones: 23357 (3 fallidas).

| Endpoint | Peticiones | Fallos | p50 ms | p95 ms | p99 ms | RPS |
|---|---:|---:|---:|---:|---:|---:|
| `GET /api/alertas` | 4286 | 0 | 8 | 550 | 2100 | 35.8 |
| `GET /api/estanques/{id}/historial` | 2174 | 0 | 11 | 520 | 2300 | 18.2 |
| `GET /api/estanques/{id}/prediccion` | 2150 | 0 | 16 | 1100 | 2800 | 18.0 |
| `GET /api/panel` | 12724 | 0 | 45 | 2300 | 4400 | 106.3 |
| `POST /api/lecturas` | 1523 | 3 | 11 | 410 | 1900 | 12.7 |
| `login` | 500 | 0 | 420 | 4500 | 5300 | 4.2 |

Errores registrados por Locust (los más frecuentes):

- `POST /api/lecturas` × 3: RemoteDisconnected('Remote end closed connection without response')
