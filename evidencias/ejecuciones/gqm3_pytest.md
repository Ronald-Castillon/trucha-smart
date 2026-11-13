# GQM M2.3 · pruebas y cobertura de src/domain en v3.0-Inc3

| Ejecución | Valor |
|---|---|
| Dónde | GitHub Actions · workflow «Evidencias del informe» · corrida #11 |
| Enlace | https://github.com/Ronald-Castillon/trucha-smart/actions/runs/43425448824 |
| Versión del código | tag `v3.0-Inc3` @ `fdf2121` |
| Fecha (UTC) | 13/11/2026 12:31:24 |
| Código de salida | 0 |

```bash
$ python -m pytest -m "not e2e" -q -p no:warnings --cov=src/domain --cov-report=term --cov-report=xml
```

```text
................................................................................................................ [ 36%]
................................................................................................................ [ 73%]
...............................................................................                                  [100%]
==================================================== tests coverage ====================================================
___________________________________ coverage: platform linux, python 3.13.18-final-0 ___________________________________

Name                                           Stmts   Miss Branch BrPart  Cover   Missing
------------------------------------------------------------------------------------------
src/domain/errores.py                             19      0      0      0   100%
src/domain/model/alerta.py                        40      0      6      0   100%
src/domain/model/clave_integracion.py             36      0      2      0   100%
src/domain/model/estanque.py                      25      0      6      0   100%
src/domain/model/evento_seguridad.py              25      0      0      0   100%
src/domain/model/lectura_agua.py                  38      0      6      0   100%
src/domain/model/lote.py                          41      0     10      0   100%
src/domain/model/registro_alimentacion.py         18      0      4      0   100%
src/domain/model/registro_mortalidad.py           20      0      6      0   100%
src/domain/model/umbral.py                        66      0     24      0   100%
src/domain/model/usuario.py                       60      0      8      0   100%
src/domain/service/calculadora_fcr.py             49      0     10      0   100%
src/domain/service/evaluador_calidad_agua.py      25      0      2      0   100%
src/domain/service/indice_riesgo.py               43      0      6      0   100%
src/domain/service/predictor_tendencia.py         71      0     18      0   100%
src/domain/service/recomendador_racion.py         78      0     30      0   100%
src/domain/service/servicio_alertas.py            20      0      2      0   100%
src/domain/service/servicio_auditoria.py          16      0      0      0   100%
src/domain/service/servicio_estanques.py          86      0     16      0   100%
src/domain/service/servicio_historial.py          56      0     10      0   100%
src/domain/service/servicio_integraciones.py      83      0     18      0   100%
src/domain/service/servicio_lecturas.py           67      0     16      0   100%
src/domain/service/servicio_prediccion.py         27      0      2      0   100%
src/domain/service/servicio_produccion.py         62      0     10      0   100%
src/domain/service/servicio_racion.py             30      0      4      0   100%
src/domain/service/servicio_reportes.py           77      0     20      0   100%
src/domain/service/servicio_usuarios.py           66      0     16      0   100%
------------------------------------------------------------------------------------------
TOTAL                                           1244      0    252      0   100%

3 empty files skipped.
Coverage XML written to file coverage.xml
303 passed, 40 deselected in 20.24s
```
