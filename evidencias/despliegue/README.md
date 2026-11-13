# Evidencias del software en modo despliegue

Capturas tomadas con Playwright sobre la aplicación desplegada (Informe S12, sección 3.9).

## `render/` · despliegue público en Render (12/11/2026)

https://truchasmart.onrender.com · la barra superior de cada captura muestra la URL real y la hora.
En `r07_auditoria.png` se ocultaron los dos últimos octetos de la IP pública del cliente.

| Captura | Pantalla |
|---|---|
| [r01_login.png](render/r01_login.png) | Inicio de sesión |
| [r02_panel.png](render/r02_panel.png) | Panel en vivo (rol Piscicultor) |
| [r03_historial.png](render/r03_historial.png) | Historial de la Jaula J1 con índice de riesgo, predicción y modelo de IA |
| [r04_produccion.png](render/r04_produccion.png) | Producción del lote L-2026-01 y ración recomendada |
| [r05_reporte.png](render/r05_reporte.png) | Vista previa del reporte de calidad de agua |
| [r06_alertas.png](render/r06_alertas.png) | Alertas |
| [r07_auditoria.png](render/r07_auditoria.png) | Bitácora de seguridad (rol Administrador) |
| [r08_swagger.png](render/r08_swagger.png) | Swagger UI (`/docs`) |
| [r09_salud.png](render/r09_salud.png) | `/api/salud` |

## `local/` · despliegue con docker compose (06/11/2026)

http://localhost:8000 servido por los contenedores de la aplicación y PostgreSQL 16.

| Captura | Pantalla |
|---|---|
| [d1_login.png](local/d1_login.png) | Inicio de sesión |
| [d2_panel.png](local/d2_panel.png) | Panel en vivo |
| [d3_historial.png](local/d3_historial.png) | Historial de la Jaula J1 |
| [d4_alertas.png](local/d4_alertas.png) | Alertas |
| [d5_auditoria.png](local/d5_auditoria.png) | Bitácora de seguridad |
| [d6_swagger.png](local/d6_swagger.png) | Swagger UI |
| [d7_salud.png](local/d7_salud.png) | `/api/salud` |
