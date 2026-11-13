# GQM M3.2 · indicadores de valor TO-BE medidos sobre v1.0-PMV

| Ejecución | Valor |
|---|---|
| Dónde | GitHub Actions · workflow «Evidencias del informe» · corrida #11 |
| Enlace | https://github.com/Ronald-Castillon/trucha-smart/actions/runs/43425448824 |
| Versión del código | rama `main` @ `d13a8f6` |
| Fecha (UTC) | 13/11/2026 12:29:42 |
| Código de salida | 0 |

```bash
$ python tools/medir_indicadores.py --etiqueta github_inc1 --repo /home/runner/work/trucha-smart/tag-v1.0-PMV
```

```text
{
  "etiqueta": "github_inc1",
  "version_medida": "v1.0-PMV",
  "medido_en": "2026-11-13T12:29:43+00:00",
  "entorno": "linux, Python 3.13.18, SQLite, Chromium headless (Playwright)",
  "IV-1": {
    "descripcion": "lectura crítica (OD 4.0 mg/L) por API -> alerta CRÍTICA visible en el panel web abierto",
    "muestras_s": [
      2.321,
      1.795,
      2.298,
      1.794,
      2.296
    ],
    "promedio_s": 2.101,
    "maximo_s": 2.321,
    "valor_minutos": 0.0387,
    "criterio": "máximo de las muestras (peor caso observado)"
  },
  "IV-2": {
    "descripcion": "la versión no tiene exportación de reportes",
    "valor_horas": null
  },
  "IV-3": {
    "descripcion": "simulador escenario normal con --intervalo 5 s; lecturas registradas en la BD durante la ventana, extrapoladas a 24 h",
    "lecturas_registradas": 7,
    "ventana_s": 30.514,
    "valor_lecturas_dia": 19820.3
  }
}
Escrito docs/gqm/mediciones/medicion_github_inc1.json
```
