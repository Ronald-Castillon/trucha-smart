# GQM M2.3 · pruebas y cobertura de src/domain en v1.0-PMV

| Ejecución | Valor |
|---|---|
| Dónde | GitHub Actions · workflow «Evidencias del informe» · corrida #11 |
| Enlace | https://github.com/Ronald-Castillon/trucha-smart/actions/runs/43425448824 |
| Versión del código | tag `v1.0-PMV` @ `2cec6af` |
| Fecha (UTC) | 13/11/2026 12:29:31 |
| Código de salida | 0 |

```bash
$ python -m pytest -m "not e2e" -q -p no:warnings --cov=src/domain --cov-report=term --cov-report=xml
```

```text
................................................................................................................ [ 73%]
........................................                                                                         [100%]
==================================================== tests coverage ====================================================
___________________________________ coverage: platform linux, python 3.13.18-final-0 ___________________________________

Name                                           Stmts   Miss Branch BrPart  Cover   Missing
------------------------------------------------------------------------------------------
src/domain/errores.py                             15      0      0      0   100%
src/domain/model/alerta.py                        40      0      6      0   100%
src/domain/model/estanque.py                      25      0      6      0   100%
src/domain/model/lectura_agua.py                  38      0      6      0   100%
src/domain/model/lote.py                          41      0     10      0   100%
src/domain/model/umbral.py                        66      0     24      0   100%
src/domain/model/usuario.py                       44      0      6      0   100%
src/domain/service/evaluador_calidad_agua.py      25      0      2      0   100%
src/domain/service/servicio_alertas.py            20      0      2      0   100%
src/domain/service/servicio_estanques.py          86      0     16      0   100%
src/domain/service/servicio_lecturas.py           67      0     16      0   100%
src/domain/service/servicio_usuarios.py           37      0      6      0   100%
------------------------------------------------------------------------------------------
TOTAL                                            504      0    100      0   100%

3 empty files skipped.
Coverage XML written to file coverage.xml
152 passed, 10 deselected in 5.80s
```
