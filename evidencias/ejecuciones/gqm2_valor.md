# GQM M3.2 · indicadores de valor TO-BE medidos sobre v2.0-Inc2

| Ejecución | Valor |
|---|---|
| Dónde | GitHub Actions · workflow «Evidencias del informe» · corrida #11 |
| Enlace | https://github.com/Ronald-Castillon/trucha-smart/actions/runs/43425448824 |
| Versión del código | rama `main` @ `d13a8f6` |
| Fecha (UTC) | 13/11/2026 12:30:43 |
| Código de salida | 0 |

```bash
$ python tools/medir_indicadores.py --etiqueta github_inc2 --repo /home/runner/work/trucha-smart/tag-v2.0-Inc2
```

```text
{
  "etiqueta": "github_inc2",
  "version_medida": "v2.0-Inc2",
  "medido_en": "2026-11-13T12:30:45+00:00",
  "entorno": "linux, Python 3.13.18, SQLite, Chromium headless (Playwright)",
  "IV-1": {
    "descripcion": "lectura crítica (OD 4.0 mg/L) por API -> alerta CRÍTICA visible en el panel web abierto",
    "muestras_s": [
      1.315,
      0.789,
      1.293,
      0.79,
      1.292
    ],
    "promedio_s": 1.096,
    "maximo_s": 1.315,
    "valor_minutos": 0.0219,
    "criterio": "máximo de las muestras (peor caso observado)"
  },
  "IV-2": {
    "descripcion": "obtener el reporte mensual (octubre 2026): calidad de agua y producción en PDF y CSV por la API",
    "archivos": [
      {
        "ruta": "/api/reportes/calidad-agua.pdf?desde=2026-10-01&hasta=2026-10-31",
        "bytes": 16997
      },
      {
        "ruta": "/api/reportes/calidad-agua.csv?desde=2026-10-01&hasta=2026-10-31",
        "bytes": 12901
      },
      {
        "ruta": "/api/reportes/produccion.pdf?desde=2026-10-01&hasta=2026-10-31",
        "bytes": 3048
      },
      {
        "ruta": "/api/reportes/produccion.csv?desde=2026-10-01&hasta=2026-10-31",
        "bytes": 442
      }
    ],
    "segundos": 0.098,
    "valor_horas": 2.7e-05
  },
  "IV-3": {
    "descripcion": "simulador escenario normal con --intervalo 5 s; lecturas registradas en la BD durante la ventana, extrapoladas a 24 h",
    "lecturas_registradas": 7,
    "ventana_s": 30.507,
    "valor_lecturas_dia": 19824.9
  }
}
Escrito docs/gqm/mediciones/medicion_github_inc2.json
```
