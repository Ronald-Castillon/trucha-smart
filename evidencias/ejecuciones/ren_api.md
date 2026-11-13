# Render · API REST pública: login JWT, panel y riesgo del modelo de IA

| Ejecución | Valor |
|---|---|
| Dónde | GitHub Actions · workflow «Evidencias del informe» · corrida #11 |
| Enlace | https://github.com/Ronald-Castillon/trucha-smart/actions/runs/43425448824 |
| Versión del código | rama `main` @ `d13a8f6` |
| Fecha (UTC) | 13/11/2026 12:35:29 |
| Código de salida | 0 |

```bash
$ python tools/evidencias/render_api.py
```

```text
POST /api/auth/login -> 200  usuario=piscicultor rol=PISCICULTOR token=eyJhbGciOiJIUzI1NiIs...
GET /api/panel -> 200  estanques: ['aaaa', 'Dr. Carlos Mendoza Ríos', 'esss', 'estanque', 'Estanque A1', 'Estanque A2', 'estanque video', 'Jaula J1']
GET /api/estanques/3/riesgo-modelo -> 200
{
 "estanque_id": 3,
 "estanque": "Jaula J1",
 "nivel": "ALTO",
 "probabilidad": 1.0,
 "factores": [
  {
   "nombre": "tendencia de la temperatura (6 h)",
   "aporte": 1411.724
  },
  {
   "nombre": "tendencia del oxígeno (6 h)",
   "aporte": 1367.593
  },
  {
   "nombre": "margen de temperatura bajo el límite",
   "aporte": 1.409
  }
 ],
 "version_modelo": "riesgo-v1",
 "puntos": 24,
 "basada_en_hasta": "2026-11-13T12:27:08.697861Z",
 "mensaje": "Probabilidad de evento crítico en 6 h: 100% (ALTO)",
 "aviso": "Prototipo entrenado con datos sintéticos: no reemplaza las alertas por umbral ni la decisión del técnico (ver models/riesgo/tarjeta_modelo_v1.md)."
}
```
