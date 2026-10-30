# Prueba de carga (RNF-P) — resultado medido

Generado por `tools/prueba_carga.py` el 2026-10-30T04:24:55+00:00 con Locust (Windows 11, 20 núcleos, 31.8 GB, BD sqlite, 4 workers uvicorn). Locust y la API se ejecutan en la misma máquina y comparten CPU.

Carga: **500 usuarios concurrentes** (rampa 25.0/s) durante 120 s; escenario tests/carga/locustfile.py (90 % consulta, 10 % sensores).

| Métrica | Valor medido | Meta (guía S10) | ¿Cumple? |
|---|---:|---:|:---:|
| Latencia p95 | 4300 ms | < 800 ms | No |
| Tasa de errores | 0.728 % | < 1.0 % | Sí |
| Throughput | 107.1 RPS | — | — |
| Latencia p50 / p99 | 1200 / 7900 ms | — | — |
| Memoria del servidor (promedio / máx.) | 476.7 / 502.4 MB | — | — |
| CPU del servidor (máx., suma de workers) | 1622.5 % | — | — |

Peticiones: 12908 (94 fallidas).

| Endpoint | Peticiones | Fallos | p50 ms | p95 ms | p99 ms | RPS |
|---|---:|---:|---:|---:|---:|---:|
| `GET /api/alertas` | 2282 | 17 | 530 | 2400 | 4800 | 18.9 |
| `GET /api/estanques/{id}/historial` | 1171 | 7 | 580 | 2600 | 5200 | 9.7 |
| `GET /api/estanques/{id}/prediccion` | 1142 | 7 | 830 | 2800 | 5000 | 9.5 |
| `GET /api/panel` | 6727 | 49 | 2100 | 4300 | 7100 | 55.8 |
| `POST /api/lecturas` | 1086 | 14 | 530 | 2500 | 6500 | 9.0 |
| `login` | 500 | 0 | 3300 | 8900 | 28000 | 4.1 |

Errores registrados por Locust (los más frecuentes):

- `GET /api/panel` × 45: RemoteDisconnected('Remote end closed connection without response')
- `GET /api/alertas` × 16: RemoteDisconnected('Remote end closed connection without response')
- `POST /api/lecturas` × 9: ConnectionResetError(10054, 'Se ha forzado la interrupci�n de una conexi�n existente por el host remoto', None, 10054, None)
- `GET /api/estanques/{id}/prediccion` × 7: RemoteDisconnected('Remote end closed connection without response')
- `GET /api/estanques/{id}/historial` × 7: RemoteDisconnected('Remote end closed connection without response')
- `POST /api/lecturas` × 4: RemoteDisconnected('Remote end closed connection without response')
- `GET /api/panel` × 4: ConnectionResetError(10054, 'Se ha forzado la interrupci�n de una conexi�n existente por el host remoto', None, 10054, None)
- `POST /api/lecturas` × 1: ConnectionAbortedError(10053, 'Se ha anulado una conexi�n establecida por el software en su equipo host', None, 10053, None)
- `GET /api/alertas` × 1: ConnectionResetError(10054, 'Se ha forzado la interrupci�n de una conexi�n existente por el host remoto', None, 10054, None)
