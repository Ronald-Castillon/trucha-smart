# Render · API REST pública: login JWT, panel y riesgo del modelo de IA

| Ejecución | Valor |
|---|---|
| Dónde | GitHub Actions · workflow «Evidencias del informe» · corrida #4 |
| Enlace | https://github.com/Ronald-Castillon/trucha-smart/actions/runs/43368473703 |
| Versión del código | rama `main` @ `f80fe18` |
| Fecha (UTC) | 13/11/2026 04:58:19 |
| Código de salida | 0 |

```bash
$ python tools/evidencias/render_api.py
```

```text
POST /api/auth/login -> 200  usuario=piscicultor rol=PISCICULTOR token=eyJhbGciOiJIUzI1NiIs...
GET /api/panel -> 200  estanques: ['aaaa', 'Dr. Carlos Mendoza Ríos', 'esss', 'Estanque A1', 'Estanque A2', 'Jaula J1']
GET /api/estanques/3/riesgo-modelo -> 200
{
 "estanque_id": 3,
 "estanque": "Jaula J1",
 "nivel": "BAJO",
 "probabilidad": 0.0342,
 "factores": [
  {
   "nombre": "margen de oxígeno sobre el límite",
   "aporte": 2.951
  },
  {
   "nombre": "tendencia del oxígeno (6 h)",
   "aporte": 1.133
  },
  {
   "nombre": "pH actual",
   "aporte": 0.158
  }
 ],
 "version_modelo": "riesgo-v1",
 "puntos": 9,
 "basada_en_hasta": "2026-10-22T21:00:00Z",
 "mensaje": "Probabilidad de evento crítico en 6 h: 3% (BAJO)",
 "aviso": "Prototipo entrenado con datos sintéticos: no reemplaza las alertas por umbral ni la decisión del técnico (ver models/riesgo/tarjeta_modelo_v1.md)."
}
```
