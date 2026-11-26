# Análisis estático con SciTools Understand (guía S14)

Generado por `tools/understand/analizar.ps1` en GitHub Actions (26/11/2026 22:51 UTC). Corrida: https://github.com/Ronald-Castillon/trucha-smart/actions/runs/45907381048

Alcance: `src/` (arquitectura hexagonal) y `tools/`, lenguaje Python. Herramienta: SciTools Understand 8.1 con licencia educativa, en el runner propio del equipo.

## 1. Métricas del proyecto

| Métrica | Valor |
|---|---|
| Archivos de código (Module File) | 112 |
| Clases | 187 |
| Funciones y métodos | 573 |
| Líneas totales (CountLine) | 10497 |
| Líneas de código (CountLineCode) | 8214 |
| Líneas de comentario (CountLineComment) | 656 |
| Relación comentario/código | 0.08 |
| Complejidad ciclomática promedio por función | 1.88 |
| Complejidad ciclomática máxima | 14 |
| Funciones con complejidad > 10 | 1 de 573 |

Entidades exportadas por tipo: Class 187, File 19, Function 547, Module File 112, Package 22, Static Function 26, Unknown Class 4.

## 2. Métricas por capa (Architecture)

| Capa | Archivos | Líneas de código | Complejidad total (SumCyclomatic) |
|---|---|---|---|
| domain | 26 | 1767 | 286 |
| ports | 27 | 459 | 81 |
| adapters | 36 | 3111 | 417 |
| main | 1 | 90 | 5 |
| tools | 18 | 2514 | 372 |
| otro | 4 | 273 | 32 |

## 3. Function Metrics · 10 funciones de mayor complejidad ciclomática

| Función | Ciclomática | Líneas de código | Anidamiento máx. |
|---|---|---|---|
| `tools.generar_seed.generar` | 14 | 134 | 3 |
| `src.domain.service.recomendador_racion.TablaAlimentacion.__post_init__` | 10 | 19 | 2 |
| `src.domain.service.predictor_tendencia.predecir` | 9 | 77 | 2 |
| `tools.gqm_metrics.m3_2` | 9 | 42 | 2 |
| `resumen.main` | 8 | 113 | 2 |
| `ejecutar.main` | 8 | 61 | 2 |
| `tools.gqm_metrics.m3_1` | 8 | 32 | 3 |
| `src.adapters.inbound.rest.lecturas.estado_panel` | 8 | 29 | 1 |
| `tools.contraste_paleta.main` | 8 | 22 | 2 |
| `tools.check_domain_purity.analizar_modulo` | 8 | 18 | 3 |

## 4. Class Metrics · 10 clases con más acoplamiento

| Clase | Acoplamiento (CBO) | Métodos | Herencia máx. | Líneas de código |
|---|---|---|---|---|
| `src.domain.service.servicio_integraciones.ServicioIntegraciones` | 25 | 9 | 0 | 94 |
| `src.domain.service.servicio_reportes.ServicioReportes` | 25 | 5 | 0 | 134 |
| `src.adapters.inbound.rest.dependencias.Contenedor` | 24 | 20 | 0 | 110 |
| `src.domain.service.servicio_historial.ServicioHistorial` | 20 | 4 | 0 | 57 |
| `src.domain.service.servicio_lecturas.ServicioLecturas` | 19 | 7 | 0 | 88 |
| `src.domain.service.servicio_produccion.ServicioProduccion` | 18 | 9 | 0 | 83 |
| `src.domain.service.servicio_estanques.ServicioEstanques` | 16 | 15 | 0 | 102 |
| `src.domain.service.servicio_usuarios.ServicioUsuarios` | 16 | 8 | 0 | 73 |
| `src.domain.service.riesgo_modelo.ServicioRiesgoModelo` | 14 | 2 | 0 | 65 |
| `src.domain.service.servicio_racion.ServicioRacion` | 12 | 2 | 0 | 31 |

## 5. Dependencies · dependencias entre capas

Referencias desde la capa de la fila hacia la capa de la columna:

| Desde \ Hacia | domain | ports | adapters | main | tools |
|---|---|---|---|---|---|
| domain | 412 | 194 | · | · | · |
| ports | 243 | 4 | · | · | · |
| adapters | 422 | 77 | 668 | · | · |
| main | · | · | 84 | · | · |
| tools | 26 | · | 6 | 3 | 22 |

**Regla de la arquitectura hexagonal (ADR-001, contratos de import-linter en pyproject.toml):** `domain` y `ports` no dependen de `adapters` ni de `main`. Dependencias que la violan según Understand: **0**.

## 6. Archivos del reporte

| Archivo | Contenido |
|---|---|
| [metricas.csv](metricas.csv) | Todas las métricas por entidad (`und metrics`) |
| [dependencias_archivos.csv](dependencias_archivos.csv) | Dependencias entre archivos (`und export -dependencies file csv`) |
| [dependencias_clases.csv](dependencias_clases.csv) | Dependencias entre clases (`und export -dependencies class csv`) |
| [reporte_understand.txt](reporte_understand.txt) | Reportes Project/File/Class/Class OO/Program Unit Metrics, Complexity e Imports (`und report`) |
| [html/](html/) | Los mismos reportes en HTML |
| [analisis.sarif](analisis.sarif) | Errores y advertencias del análisis (`und analyze -sarif`) |
