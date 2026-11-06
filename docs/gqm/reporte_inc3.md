# Reporte GQM — Incremento 3

Generado por `tools/gqm_metrics.py --incremento 3` el 2026-11-05 22:56.
Los valores se calculan a partir de artefactos reales del repositorio (código, coverage.xml, evidencias/, Issues/defectos.csv, docs/gqm/*.yaml).

| Métrica | Nombre | Valor | Meta | Estado |
|---|---|---|---|---|
| M1.1 | Pureza del dominio | 0.0 % | <= 0.0 % | ✅ cumple |
| M1.2 | Componentes hexagonales conformes | 100 % | >= 100 % | ✅ cumple |
| M2.1 | Evidencias de aceptación | 100 % | >= 100 % | ✅ cumple |
| M2.2 | Densidad de defectos | 1.33 Def/RF | <= 0.20 Def/RF | ❌ no cumple |
| M2.3 | Cobertura de src/domain (líneas) | 100.0 % | >= 80.0 % | ✅ cumple |
| M3.1 | Brechas AS-IS resueltas | 100 % | >= 100 % | ✅ cumple |
| M3.2 | Mejora de indicadores de valor | 100.0 % (AS-IS estimado: IV-1, IV-3; parcial 2 de 3 IV) | >= 80.0 % | ⚠️ no acredita (requiere AS-IS medido) |

## Detalle

- **M1.1** — 0 de 30 módulos de src/domain importan fuera de stdlib
- **M1.2** — domain/model: OK; domain/service: OK; ports/inbound: OK; ports/outbound: OK; adapters (inbound + outbound): OK; import-linter: OK
- **M2.1** — 6 de 6 capturas en evidencias/inc3/
- **M2.2** — 4 defectos / 3 RF · fuente: GitHub Issues (label bug + inc3) · #42 RNF-P: la meta p95 < 800 ms con 500 usuarios no se cumple con PostgreSQL en el runner de CI (4 núcleos); #39 Defecto: errores 500 'database is locked' con SQLite bajo carga concurrente; #38 Defecto: tablas desplazables no accesibles por teclado (axe scrollable-region-focusable); #36 Defecto: contraste insuficiente en etiquetas verde y ámbar (axe-core, WCAG 1.4.3)
- **M2.3** — 1244 de 1244 líneas ejecutables cubiertas
- **M3.1** — 10 de 10 resueltas y verificadas: B-01, B-02, B-03, B-04, B-05, B-06, B-07, B-08, B-09, B-10
- **M3.2** — IV-1: 720 (AS-IS estimado) → 0.0225 minutos (100.0 %); IV-2: pendiente (falta AS-IS); IV-3: 2 (AS-IS estimado) → 19716.5 lecturas/día (100.0 %)
