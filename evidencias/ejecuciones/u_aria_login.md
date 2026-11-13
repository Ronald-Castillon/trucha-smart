# U · WCAG 4.1.2: árbol de accesibilidad de /login

| Ejecución | Valor |
|---|---|
| Dónde | GitHub Actions · workflow «Evidencias del informe» · corrida #11 |
| Enlace | https://github.com/Ronald-Castillon/trucha-smart/actions/runs/43425448824 |
| Versión del código | rama `main` @ `d13a8f6` |
| Fecha (UTC) | 13/11/2026 12:35:20 |
| Código de salida | 0 |

```bash
$ python tools/evidencias/aria.py login
```

```text
Árbol de accesibilidad de /login (lo que anuncia un lector de pantalla):

- link "Saltar al contenido":
  - /url: "#contenido"
- main:
  - heading "🐟 TruchaSmart" [level=1]
  - paragraph: Monitoreo de calidad de agua y producción de trucha
  - text: Usuario
  - textbox "Usuario"
  - text: Contraseña
  - textbox "Contraseña"
  - button "Ingresar"
```
