# U · WCAG 1.4.1: texto que acompaña a cada color de estado

| Ejecución | Valor |
|---|---|
| Dónde | GitHub Actions · workflow «Evidencias del informe» · corrida #4 |
| Enlace | https://github.com/Ronald-Castillon/trucha-smart/actions/runs/43368473703 |
| Versión del código | rama `main` @ `f80fe18` |
| Fecha (UTC) | 13/11/2026 04:58:06 |
| Código de salida | 0 |

```bash
$ python tools/evidencias/aria.py color
```

```text
WCAG 1.4.1: cada color de estado va acompañado de texto (no se depende solo del color)

/panel
  clase=riesgo verde           fondo=rgb(23, 119, 63)     texto visible=«Riesgo 0 · bajo»
  clase=PRECAUCION             fondo=rgb(242, 201, 76)    texto visible=«Predicción»
  clase=NORMAL                 fondo=rgb(23, 119, 63)     texto visible=«Sin alertas abiertas»
  clase=riesgo verde           fondo=rgb(23, 119, 63)     texto visible=«Riesgo 15 · bajo»
  clase=PRECAUCION             fondo=rgb(242, 201, 76)    texto visible=«PRECAUCIÓN»

/alertas
  clase=PRECAUCION             fondo=rgb(242, 201, 76)    texto visible=«PRECAUCIÓN»
```
