# Confiabilidad (R) y rendimiento (P) — FURPS+

Issue #31 (RNF-R/P) · defecto encontrado y corregido: #39 · Incremento 3

Todos los valores de este documento fueron **medidos** con las herramientas del repositorio; los
archivos de resultado se generan solos y no se editan a mano.

| Archivo | Contenido |
|---|---|
| [`confiabilidad.md`](confiabilidad.md) / `.json` | Última prueba de caos local (SQLite) |
| [`rendimiento.md`](rendimiento.md) / `.json` | Última prueba de carga local (SQLite) |
| [`historial/`](historial/) | Corridas intermedias de la investigación del defecto #39 |
| Artefacto `confiabilidad-rendimiento` del job de CI | Las mismas pruebas contra **PostgreSQL 16**, incluida la caída de la BD |

## 1. Confiabilidad: inyección de fallos

`python tools/prueba_confiabilidad.py --duracion 300 --fallos 5`

Un supervisor reinicia la API cuando el proceso muere (como `restart: always`); se mata el proceso
5 veces en 5 minutos y una sonda consulta `GET /api/salud` cada 250 ms. `/api/salud` comprueba la
base de datos y responde **503 sin caerse** si no está disponible (prueba
`test_salud_responde_503_sin_caerse_si_la_bd_no_esta`).

| Métrica | Fórmula | Medido (local) | Meta guía S10 | ¿Cumple? |
|---|---|---:|---:|:---:|
| MTTR | promedio (primer 200 tras el fallo − instante del fallo) | 1.8 s | < 5 min | Sí |
| MTBF | tiempo en servicio / fallos | 58.2 s (forzado) | — | — |
| Disponibilidad en la prueba | (duración − tiempo caído) / duración | 96.99 % | ≥ 99.5 % | No (ver nota) |
| Disponibilidad en régimen | MTBF / (MTBF + MTTR) | ≥ 99.5 % con hasta **372 caídas/día** | ≥ 99.5 % | Condicionado |

**Nota honesta:** la prueba fuerza un fallo por minuto para medir la recuperación; con esa tasa
artificial la disponibilidad medida (96.99 %) no alcanza 99.5 %. Lo que la prueba demuestra es la
recuperación automática en < 2 s; la meta de 99.5 % se cumple mientras haya menos de 372 caídas
del proceso por día, lo que no puede comprobarse sin operar el sistema en producción.

Durante el desarrollo de la herramienta se corrigieron dos sesgos de medición que inflaban el
resultado (primera versión: 99.58 %): en Windows una sonda a un puerto cerrado espera 1–2 s, por
lo que contar sondas y fechar la recuperación al *enviar* la sonda subestimaba la caída. Ahora la
disponibilidad se calcula por tiempo y la recuperación con el instante de la respuesta.

En CI se agrega la caída de PostgreSQL (`docker stop` 10 s y `docker start`): se verifica que la
API responda 503 durante la caída y se mide el tiempo hasta volver a 200 (reconexión automática con
`pool_pre_ping`).

## 2. Rendimiento: prueba de carga con Locust (equivalente a k6/JMeter)

`python tools/prueba_carga.py --usuarios 500 --tasa 25 --duracion 120 --workers 8`

Escenario `tests/carga/locustfile.py`: 90 % de usuarios con el panel abierto (panel, alertas,
historial, predicción) y 10 % de sensores registrando lecturas; cada usuario inicia sesión al
entrar. Locust y la API comparten la misma máquina (Windows 11, 20 núcleos).

### Evolución (todas con 500 usuarios, rampa 25/s, 120 s, SQLite)

| # | Cambio | Workers | p95 | Errores | RPS | ¿Cumple p95 < 800 ms y errores < 1 %? |
|---|---|---:|---:|---:|---:|:---:|
| 1 | Línea base | 4 | 58 000 ms | 4.06 % | 45.5 | No |
| 2 | Defecto #39: SQLite en WAL + `busy_timeout`; pool de conexiones 20 + 30 | 4 | 4 300 ms | 0.73 % | 107.1 | No (p95) |
| 3 | Igual que 2 | 8 | 1 900 ms | 0.013 % | 195.2 | No (p95) |
| 4 | El panel reutiliza el estado leído para el índice de riesgo (35 → 26 consultas por petición) | 8 | **390 ms** | **0.016 %** | **206.3** | **Sí** |

La corrida 1 está documentada en el Issue #39 (su archivo fue sobrescrito por la corrida 2, antes
de guardar el historial); las corridas 2 y 3 están en `historial/`; la 4 es `rendimiento.md`.

### Causas encontradas (defecto #39)

1. `sqlite3.OperationalError: database is locked`: con el diario por defecto, cada escritura
   (logins que registran la bitácora, lecturas de sensores) bloqueaba a los lectores ⇒ errores 500.
2. `QueuePool limit of size 5 overflow 10 reached`: cada worker atiende hasta 40 peticiones a la vez
   con solo 15 conexiones ⇒ esperas de 30 s y errores 500.
3. Al activar WAL, varios workers arrancando a la vez chocaban al cambiar el modo; se fija
   `busy_timeout` antes de `journal_mode`.

### Límites

- SQLite es la base de desarrollo; producción usa PostgreSQL (ADR-003), medido en CI con 4 workers
  en el runner de GitHub (4 núcleos), por lo que sus valores no son comparables uno a uno con los
  locales.
- La corrida es de 2 minutos; no es una prueba de resistencia (*soak*) de horas.
