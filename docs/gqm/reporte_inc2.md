# Reporte GQM — Incremento 2

Generado por `tools/gqm_metrics.py --incremento 2` el 2026-10-23 02:40.
Los valores se calculan a partir de artefactos reales del repositorio (código, coverage.xml, evidencias/, Issues/defectos.csv, docs/gqm/*.yaml).

| Métrica | Nombre | Valor | Meta | Estado |
|---|---|---|---|---|
| M1.1 | Pureza del dominio | 0.0 % | <= 0.0 % | ✅ cumple |
| M1.2 | Componentes hexagonales conformes | 100 % | >= 100 % | ✅ cumple |
| M2.1 | Evidencias de aceptación | 100 % | >= 100 % | ✅ cumple |
| M2.2 | Densidad de defectos | 0.25 Def/RF | <= 0.20 Def/RF | ❌ no cumple |
| M2.3 | Cobertura de src/domain (líneas) | 100.0 % | >= 80.0 % | ✅ cumple |
| M3.1 | Brechas AS-IS resueltas | 90 % | >= 90 % | ✅ cumple |
| M3.2 | Mejora de indicadores de valor | 100.0 % (AS-IS estimado: IV-1, IV-3; parcial 2 de 3 IV) | >= 80.0 % | ⚠️ no acredita (requiere AS-IS medido) |

## Detalle

- **M1.1** — 0 de 24 módulos de src/domain importan fuera de stdlib
- **M1.2** — domain/model: OK; domain/service: OK; ports/inbound: OK; ports/outbound: OK; adapters (inbound + outbound): OK; import-linter: OK
- **M2.1** — 8 de 8 capturas en evidencias/inc2/
- **M2.2** — 1 defectos / 4 RF · fuente: GitHub Issues (label bug + inc2) · #19 Bug: con SQLite, las lecturas del seed a las 00:00:00 quedan fuera de los filtros por fecha
- **M2.3** — 935 de 935 líneas ejecutables cubiertas
- **M3.1** — 9 de 10 resueltas y verificadas: B-01, B-02, B-03, B-04, B-05, B-06, B-07, B-08, B-09
- **M3.2** — IV-1: 720 (AS-IS estimado) → 0.0229 minutos (100.0 %); IV-2: pendiente (falta AS-IS); IV-3: 2 (AS-IS estimado) → 19759.5 lecturas/día (100.0 %)
