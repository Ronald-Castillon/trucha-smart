# Plan GQM (Goal–Question–Metric) — TruchaSmart

| Objetivo | Pregunta | Métrica | Fórmula | Fuente | Meta Inc 1 | Meta Inc 2 |
|---|---|---|---|---|---|---|
| G1 Calidad arquitectónica | ¿El dominio está aislado de frameworks? | M1.1 Pureza | módulos contaminados / total × 100 | `tools/check_domain_purity.py` | 0 % | 0 % |
| | ¿Existen los componentes hexagonales y respetan las reglas? | M1.2 Conformidad | componentes presentes y conformes / 5 × 100 | estructura `src/` + import-linter | 100 % | 100 % |
| G2 Calidad del producto | ¿Cada RF tiene evidencia de aceptación? | M2.1 Evidencias | capturas existentes / esperadas × 100 | `evidencias/incN/` | 100 % | 100 % |
| | ¿Cuántos defectos se encuentran por RF? | M2.2 Densidad | Issues `bug`+`incN` / RF del incremento | GitHub Issues o `defectos.csv` | <= 1.0 | <= 0.2 |
| | ¿Cuánto del dominio está probado? | M2.3 Cobertura | líneas cubiertas / ejecutables de `src/domain` | `coverage.xml` | >= 80 % | >= 80 % |
| G3 Valor para el negocio | ¿Cuántas brechas AS-IS se cerraron? | M3.1 Brechas | brechas resueltas y verificadas / 10 × 100 | `brechas.yaml` + evidencias + pruebas | >= 60 % | >= 90 % |
| | ¿Cuánto mejoran los indicadores de valor? | M3.2 Mejora | promedio de mejora % de IV-1..IV-3 | `valor_indicadores.yaml` (AS-IS del equipo) | >= 50 % | >= 80 % |

Las líneas base AS-IS **deben** medirse en la piscigranja y registrarse en
`docs/gqm/valor_indicadores.yaml`. Mientras falten, M3.2 se reporta como "pendiente".

Ejecución: `python tools/gqm_metrics.py --incremento 1` → `docs/gqm/reporte_inc1.md`.
