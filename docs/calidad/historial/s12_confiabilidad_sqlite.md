# Prueba de confiabilidad (RNF-R) — resultado medido

Generado por `tools/prueba_confiabilidad.py` el 2026-11-06T20:17:16+00:00 (Windows 11, Python 3.13.16, BD sqlite).

| Métrica | Valor medido | Meta (guía S10) | ¿Cumple? |
|---|---:|---:|:---:|
| Disponibilidad (1 - tiempo caído / duración) | 94.239 % | ≥ 99.5 % | No |
| MTTR (fallo → primer 200) | 1.72 s | < 300 s | Sí |
| MTBF (tiempo en servicio / fallos) | 28.2 s | — | — |

- Duración: 90.0 s; fallos inyectados (kill del proceso): 3; reinicios del supervisor: 3.
- Sondas `GET /api/salud` cada 0.25 s: 344 en total, 343 con 200 (99.709 %; métrica secundaria, ver nota en el código).
- Tiempo de recuperación de cada fallo (s): [1.81, 1.73, 1.63].

## Interpretación

La prueba fuerza **un fallo cada 28.2 s** aprox., una tasa mucho mayor que la
real, para medir la recuperación. En régimen estable la disponibilidad es
A = MTBF / (MTBF + MTTR); con el MTTR medido, la meta de 99.5 % (432 s de caída al día)
se mantiene con hasta **251 caídas del proceso por día**.

**Alcance:** recuperación ante caídas del proceso y de la BD en un servidor con
supervisor; no reemplaza una medición de disponibilidad en producción durante meses.
