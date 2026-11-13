# F · Pruebas E2E de aceptación de cada requisito funcional

| Ejecución | Valor |
|---|---|
| Dónde | GitHub Actions · workflow «Evidencias del informe» · corrida #4 |
| Enlace | https://github.com/Ronald-Castillon/trucha-smart/actions/runs/43368473703 |
| Versión del código | tag `v3.0-Inc3` @ `fdf2121` |
| Fecha (UTC) | 13/11/2026 04:55:56 |
| Código de salida | 0 |

```bash
$ python -m pytest tests/e2e -m e2e -p no:warnings -v -k "rf"
```

```text
================================================= test session starts ==================================================
platform linux -- Python 3.13.18, pytest-9.2.0, pluggy-1.7.0 -- /opt/hostedtoolcache/Python/3.13.18/x64/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/trucha-smart/tag-v3.0-Inc3
configfile: pyproject.toml
plugins: cov-7.1.0, platformdirs-4.14.5, anyio-4.16.0
collecting ... collected 40 items / 19 deselected / 21 selected

tests/e2e/test_rf01_autenticacion.py::test_cp_rf01_02_credenciales_invalidas_muestran_mensaje PASSED             [  4%]
tests/e2e/test_rf01_autenticacion.py::test_cp_rf01_01_login_operario_llega_al_panel PASSED                       [  9%]
tests/e2e/test_rf02_estanques.py::test_cp_rf02_01_crear_estanque_y_sembrar_lote PASSED                           [ 14%]
tests/e2e/test_rf02_estanques.py::test_cp_rf02_02_lote_con_cero_peces_es_rechazado PASSED                        [ 19%]
tests/e2e/test_rf03_lecturas.py::test_cp_rf03_01_lectura_manual_visible_en_panel PASSED                          [ 23%]
tests/e2e/test_rf03_lecturas.py::test_cp_rf03_01_lectura_del_sensor_aparece_sin_recargar PASSED                  [ 28%]
tests/e2e/test_rf03_lecturas.py::test_cp_rf03_02_valor_imposible_muestra_error PASSED                            [ 33%]
tests/e2e/test_rf04_alertas.py::test_cp_rf04_01_alerta_critica_visible_en_panel PASSED                           [ 38%]
tests/e2e/test_rf04_alertas.py::test_cp_rf04_02_operario_atiende_alerta PASSED                                   [ 42%]
tests/e2e/test_rf05_historial.py::test_cp_rf05_01_y_02_historial_tendencia_y_riesgo PASSED                       [ 47%]
tests/e2e/test_rf06_produccion.py::test_cp_rf06_02_fcr_no_calculable_sin_ganancia PASSED                         [ 52%]
tests/e2e/test_rf06_produccion.py::test_cp_rf06_01_registrar_alimentacion_y_mortalidad PASSED                    [ 57%]
tests/e2e/test_rf07_racion.py::test_cp_rf07_01_racion_con_temperatura_en_precaucion PASSED                       [ 61%]
tests/e2e/test_rf07_racion.py::test_cp_rf07_02_oxigeno_critico_suspende_alimentacion PASSED                      [ 66%]
tests/e2e/test_rf08_reportes.py::test_cp_rf08_01_y_02_descargar_pdf_y_csv PASSED                                 [ 71%]
tests/e2e/test_rf08_reportes.py::test_cp_rf08_02_rango_invertido PASSED                                          [ 76%]
tests/e2e/test_rf09_integraciones.py::test_cp_rf09_01_y_02_clave_de_integracion PASSED                           [ 80%]
tests/e2e/test_rf10_prediccion.py::test_cp_rf10_01_y_02_prediccion_en_el_panel PASSED                            [ 85%]
tests/e2e/test_rf11_seguridad.py::test_cp_rf11_01_y_02_bloqueo_y_auditoria PASSED                                [ 90%]
tests/e2e/test_vivo_interfaz.py::test_panel_en_vivo_con_simulador_web PASSED                                     [ 95%]
tests/e2e/test_vivo_interfaz.py::test_lista_de_alertas_se_actualiza_sola PASSED                                  [100%]

========================================== 21 passed, 19 deselected in 40.63s ==========================================
```
