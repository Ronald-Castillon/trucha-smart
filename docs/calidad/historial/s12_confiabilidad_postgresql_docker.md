# Prueba de confiabilidad (RNF-R) — resultado medido

Generado por `tools/prueba_confiabilidad.py` el 2026-11-07T01:50:50+00:00 (Windows 11, Python 3.13.16, BD postgresql+psycopg).

| Métrica | Valor medido | Meta (guía S10) | ¿Cumple? |
|---|---:|---:|:---:|
| Disponibilidad (1 - tiempo caído / duración) | 95.581 % | ≥ 99.5 % | No |
| MTTR (fallo → primer 200) | 1.98 s | < 300 s | Sí |
| MTBF (tiempo en servicio / fallos) | 42.9 s | — | — |

- Duración: 90.0 s; fallos inyectados (kill del proceso): 2; reinicios del supervisor: 2.
- Sondas `GET /api/salud` cada 0.25 s: 308 en total, 305 con 200 (99.026 %; métrica secundaria, ver nota en el código).
- Tiempo de recuperación de cada fallo (s): [1.76, 2.21].

## Caída de PostgreSQL

- PostgreSQL detenido 10.5 s; respuestas de `/api/salud` durante la caída: {'0': 1, '503': 1} (la API NO).
- Reconexión automática (pool_pre_ping): primer 200 a los 0.52 s de `docker start` (incluye el arranque de PostgreSQL).

## Interpretación

La prueba fuerza **un fallo cada 42.9 s** aprox., una tasa mucho mayor que la
real, para medir la recuperación. En régimen estable la disponibilidad es
A = MTBF / (MTBF + MTTR); con el MTTR medido, la meta de 99.5 % (432 s de caída al día)
se mantiene con hasta **218 caídas del proceso por día**.

**Alcance:** recuperación ante caídas del proceso y de la BD en un servidor con
supervisor; no reemplaza una medición de disponibilidad en producción durante meses.
