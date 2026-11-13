# Análisis estático con SonarQube

Issue #54 · 12/11/2026 · SonarQube Community Build 26.11.0 (servidor local en Docker) ·
alcance: `src/` (Python, plantillas HTML y JavaScript de la web) y `tools/`, con pruebas en `tests/`.

## Cómo se ejecuta

```bash
docker run -d --name sonarqube -p 9000:9000 sonarqube:community   # http://localhost:9000
python tools/cobertura_sonar.py                                   # pruebas + coverage-sonar.xml
docker run --rm -e SONAR_HOST_URL=http://host.docker.internal:9000 -e SONAR_TOKEN=<token> \
  -v "$PWD:/usr/src" sonarsource/sonar-scanner-cli                 # lee sonar-project.properties
```

El token se genera en SonarQube (*My Account → Security*) y no se guarda en el repositorio.

## Resultados: antes y después de la corrección

| Medida | Antes (`680f864`, main) | Después (`e208ac3`) |
|---|---|---|
| Puerta de calidad (*Sonar way*) | Aprobada | Aprobada |
| Líneas de código (ncloc) | 8 531 | 8 559 |
| Errores (*bugs*) · confiabilidad | 4 · **C** | 0 · **A** |
| Vulnerabilidades · seguridad | 3 · **C** | 0 · **A** |
| *Code smells* · mantenibilidad | 12 · A (57 min de deuda) | 0 · A (0 min) |
| *Security hotspots* | 0 | 0 |
| Cobertura (líneas y ramas) | 93.2 % | 93.2 % |
| Duplicación | 0.0 % | 0.0 % |
| Hallazgos abiertos | 19 | 0 |

## Revisión de los 19 hallazgos

| Regla | Dónde | Cant. | Decisión |
|---|---|---|---|
| javascript:S9383 promesa sin manejar | `static/panel.js` (`alternarSimulacion`) | 1 | **Defecto corregido.** Sin conexión, la promesa quedaba rechazada sin aviso; ahora se captura y se muestra un mensaje. |
| javascript:S9383 promesa sin manejar | `static/vivo.js` (`cargarNombres`) | 1 | **Defecto corregido.** El fallo de red se captura; las alertas se anuncian igual con el id del estanque. |
| javascript:S9383 promesa sin manejar | `static/panel.js` (`refrescar()` ×2) | 2 | Sin falla real: `refrescar()` captura sus errores. Se marca con `void` para dejar explícita la intención. |
| Web:S5725 recurso de CDN sin SRI | `panel.html`, `historial.html` | 2 | **Corregido.** Chart.js 4.4.1 con `integrity="sha384-…"` y `crossorigin="anonymous"` (OWASP A08:2025). Verificado: con el hash alterado el navegador bloquea el script. |
| Web:S6845 `tabindex` en elemento no interactivo | tablas de 9 plantillas | 11 | **Excepción justificada.** El `tabindex="0"` de las tablas desplazables lo exige WCAG 2.1.1 (regla de axe-core `scrollable-region-focusable`, defecto #38). |
| python:S2245 generador pseudoaleatorio | `tools/entrenar_modelo_riesgo.py` | 1 | **Excepción justificada.** `random.Random(semilla)` genera datos sintéticos reproducibles; no es criptográfico. |
| python:S3516 función que siempre devuelve lo mismo | `tools/init_db.py` (`main`) | 1 | **Excepción justificada.** Es el código de salida del CLI (0); los errores se propagan como excepciones. |

Las excepciones están versionadas, con su motivo, en `sonar-project.properties`
(`sonar.issue.ignore.multicriteria`), para que cualquier análisis futuro las aplique igual.

## Evidencias

- Antes: [resumen](sonarqube/antes_resumen.png) · [hallazgos](sonarqube/antes_hallazgos.png)
- Después: [resumen](sonarqube/despues_resumen.png) · [hallazgos](sonarqube/despues_hallazgos.png)
- [Actividad del proyecto](sonarqube/actividad.png): 19 → 0 hallazgos entre los análisis.

## Limitaciones

- El servidor es local y usa la base embebida de SonarQube (solo para evaluación). El análisis no
  forma parte de los 6 jobs de CI; se repite a mano con los comandos de arriba.
- La cobertura importada es la de las pruebas unitarias y de integración; las E2E no se cuentan.
