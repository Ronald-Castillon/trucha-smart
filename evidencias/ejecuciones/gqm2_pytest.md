# GQM M2.3 · pruebas y cobertura de src/domain en v2.0-Inc2

| Ejecución | Valor |
|---|---|
| Dónde | GitHub Actions · workflow «Evidencias del informe» · corrida #11 |
| Enlace | https://github.com/Ronald-Castillon/trucha-smart/actions/runs/43425448824 |
| Versión del código | tag `v2.0-Inc2` @ `7d4d9b8` |
| Fecha (UTC) | 13/11/2026 12:30:28 |
| Código de salida | 0 |

```bash
$ python -m pytest -m "not e2e" -q -p no:warnings --cov=src/domain --cov-report=term --cov-report=xml
```

```text
................................................................................................................ [ 44%]
................................................................................................................ [ 88%]
..............................                                                                                   [100%]
==================================================== tests coverage ====================================================
___________________________________ coverage: platform linux, python 3.13.18-final-0 ___________________________________

Name                                           Stmts   Miss Branch BrPart  Cover   Missing
------------------------------------------------------------------------------------------
src/domain/errores.py                             15      0      0      0   100%
src/domain/model/alerta.py                        40      0      6      0   100%
src/domain/model/estanque.py                      25      0      6      0   100%
src/domain/model/lectura_agua.py                  38      0      6      0   100%
src/domain/model/lote.py                          41      0     10      0   100%
src/domain/model/registro_alimentacion.py         18      0      4      0   100%
src/domain/model/registro_mortalidad.py           20      0      6      0   100%
src/domain/model/umbral.py                        66      0     24      0   100%
src/domain/model/usuario.py                       44      0      6      0   100%
src/domain/service/calculadora_fcr.py             49      0     10      0   100%
src/domain/service/evaluador_calidad_agua.py      25      0      2      0   100%
src/domain/service/indice_riesgo.py               43      0      6      0   100%
src/domain/service/recomendador_racion.py         78      0     30      0   100%
src/domain/service/servicio_alertas.py            20      0      2      0   100%
src/domain/service/servicio_estanques.py          86      0     16      0   100%
src/domain/service/servicio_historial.py          54      0     10      0   100%
src/domain/service/servicio_lecturas.py           67      0     16      0   100%
src/domain/service/servicio_produccion.py         62      0     10      0   100%
src/domain/service/servicio_racion.py             30      0      4      0   100%
src/domain/service/servicio_reportes.py           77      0     20      0   100%
src/domain/service/servicio_usuarios.py           37      0      6      0   100%
------------------------------------------------------------------------------------------
TOTAL                                            935      0    200      0   100%

3 empty files skipped.
Coverage XML written to file coverage.xml
254 passed, 17 deselected in 12.73s
```
