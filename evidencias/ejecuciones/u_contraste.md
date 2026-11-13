# U · Contraste de la paleta (WCAG 2.1 AA, 1.4.3)

| Ejecución | Valor |
|---|---|
| Dónde | GitHub Actions · workflow «Evidencias del informe» · corrida #4 |
| Enlace | https://github.com/Ronald-Castillon/trucha-smart/actions/runs/43368473703 |
| Versión del código | tag `v3.0-Inc3` @ `fdf2121` |
| Fecha (UTC) | 13/11/2026 04:55:26 |
| Código de salida | 0 |

```bash
$ python tools/contraste_paleta.py
```

```text
OK  13.45:1  texto           #1d2b36  sobre fondo       #f4f7f9  (texto general sobre el fondo de la página)
OK  14.47:1  texto           #1d2b36  sobre superficie  #ffffff  (texto en tarjetas)
OK   5.50:1  suave           #5b6b78  sobre superficie  #ffffff  (texto secundario (.suave, etiquetas de formulario))
OK   5.11:1  suave           #5b6b78  sobre fondo       #f4f7f9  (texto secundario fuera de tarjetas)
OK   5.81:1  #ffffff         #ffffff  sobre primario    #0b6e8a  (menú superior y botones)
OK   5.81:1  primario        #0b6e8a  sobre superficie  #ffffff  (botón secundario y enlaces)
OK   5.60:1  #ffffff         #ffffff  sobre verde       #17773f  (etiqueta / semáforo NORMAL)
OK   9.12:1  texto           #1d2b36  sobre amarillo    #f2c94c  (etiqueta / semáforo PRECAUCIÓN (texto oscuro))
OK   5.44:1  #ffffff         #ffffff  sobre rojo        #c0392b  (etiqueta / semáforo CRÍTICA, botón detener simulador)
OK   5.54:1  amarillo-texto  #8a6100  sobre superficie  #ffffff  (valor en nivel de precaución (.nivel-PRECAUCION))
OK   5.44:1  rojo            #c0392b  sobre superficie  #ffffff  (valor crítico, predicción de riesgo, bitácora)
OK   5.60:1  verde           #17773f  sobre superficie  #ffffff  (indicador 'en vivo')
OK   4.76:1  rojo            #c0392b  sobre #fdecea     #fdecea  (mensaje de error)
OK   5.00:1  verde           #17773f  sobre #e8f5ee     #e8f5ee  (mensaje de confirmación)

14/14 pares cumplen WCAG 2.1 AA (>= 4.5:1)
```
