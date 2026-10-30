# Prueba de confiabilidad (RNF-R) — resultado medido

Generado por `tools/prueba_confiabilidad.py` el 2026-10-30T04:12:10+00:00 (Windows 11, Python 3.13.16, BD sqlite).

| Métrica | Valor medido | Meta (guía S10) | ¿Cumple? |
|---|---:|---:|:---:|
| Disponibilidad (1 - tiempo caído / duración) | 96.992 % | ≥ 99.5 % | No |
| MTTR (fallo → primer 200) | 1.8 s | < 300 s | Sí |
| MTBF (tiempo en servicio / fallos) | 58.2 s | — | — |

- Duración: 300.0 s; fallos inyectados (kill del proceso): 5; reinicios del supervisor: 5.
- Sondas `GET /api/salud` cada 0.25 s: 1171 en total, 1171 con 200 (100.0 %; métrica secundaria, ver nota en el código).
- Tiempo de recuperación de cada fallo (s): [2.1, 1.76, 1.63, 1.79, 1.74].

## Interpretación

La prueba fuerza **un fallo cada 58.2 s** aprox., una tasa mucho mayor que la
real, para medir la recuperación. En régimen estable la disponibilidad es
A = MTBF / (MTBF + MTTR); con el MTTR medido, la meta de 99.5 % (432 s de caída al día)
se mantiene con hasta **240 caídas del proceso por día**.

**Alcance:** recuperación ante caídas del proceso y de la BD en un servidor con
supervisor; no reemplaza una medición de disponibilidad en producción durante meses.
