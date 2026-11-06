# Prueba de confiabilidad (RNF-R) — resultado medido

Generado por `tools/prueba_confiabilidad.py` el 2026-11-06T03:21:37+00:00 (Linux 7.0.0-1019-azure, Python 3.13.18, BD postgresql+psycopg).

| Métrica | Valor medido | Meta (guía S10) | ¿Cumple? |
|---|---:|---:|:---:|
| Disponibilidad (1 - tiempo caído / duración) | 96.872 % | ≥ 99.5 % | No |
| MTTR (fallo → primer 200) | 1.17 s | < 300 s | Sí |
| MTBF (tiempo en servicio / fallos) | 36.3 s | — | — |

- Duración: 150.0 s; fallos inyectados (kill del proceso): 4; reinicios del supervisor: 4.
- Sondas `GET /api/salud` cada 0.25 s: 600 en total, 543 con 200 (90.5 %; métrica secundaria, ver nota en el código).
- Tiempo de recuperación de cada fallo (s): [1.21, 1.11, 1.14, 1.23].

## Caída de PostgreSQL

- PostgreSQL detenido 10.1 s; respuestas de `/api/salud` durante la caída: {'503': 36} (la API siguió respondiendo 503, sin caerse).
- Reconexión automática (pool_pre_ping): primer 200 a los 0.34 s de `docker start` (incluye el arranque de PostgreSQL).

## Interpretación

La prueba fuerza **un fallo cada 36.3 s** aprox., una tasa mucho mayor que la
real, para medir la recuperación. En régimen estable la disponibilidad es
A = MTBF / (MTBF + MTTR); con el MTTR medido, la meta de 99.5 % (432 s de caída al día)
se mantiene con hasta **369 caídas del proceso por día**.

**Alcance:** recuperación ante caídas del proceso y de la BD en un servidor con
supervisor; no reemplaza una medición de disponibilidad en producción durante meses.
