# U · WCAG 4.1.2 y 2.4.1: árbol de accesibilidad del panel

| Ejecución | Valor |
|---|---|
| Dónde | GitHub Actions · workflow «Evidencias del informe» · corrida #11 |
| Enlace | https://github.com/Ronald-Castillon/trucha-smart/actions/runs/43425448824 |
| Versión del código | rama `main` @ `d13a8f6` |
| Fecha (UTC) | 13/11/2026 12:35:23 |
| Código de salida | 0 |

```bash
$ python tools/evidencias/aria.py panel
```

```text
Árbol de accesibilidad del panel: enlace de salto, navegación y tarjeta de la Jaula J1:

- link "Saltar al contenido":
  - /url: "#contenido"
- banner:
  - navigation:
    - text: 🐟 TruchaSmart
    - link "Panel":
      - /url: /panel
    - link "Estanques":
      - /url: /estanques
    - link "Registrar lectura":
      - /url: /lecturas/nueva
    - link "Alertas":
      - /url: /alertas
  - text: Olga Operaria (Operario)
  - button "Salir"
- main:
  …
- article:
  - heading "Jaula J1" [level=2]:
    - link "Jaula J1":
      - /url: /estanques/3
  - paragraph:
    - text: Riesgo 15 · bajo ·
    - link "Historial":
      - /url: /estanques/3/historial
  - paragraph: Jaula · Laguna, muelle 2
  - paragraph:
    - text: Lote
    - link "L-2026-03":
      - /url: /lotes/3/produccion
      - strong: L-2026-03
    - text: · 3000 peces · 230.0 g
  - text: "🌡️ 12.27 °C · 💧 OD 6.05 mg/L · pH 7.48 Última lectura:"
  - time: 22/10/2026 21:00:00 UTC
  - text: "PRECAUCIÓN Oxígeno disuelto en PRECAUCIÓN: 6.16 mg/L (normal >= 7 mg/L)"
  - paragraph:
    - link "Atender alertas →":
      - /url: /alertas
```
