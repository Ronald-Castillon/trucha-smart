# Evidencias ejecutadas en GitHub Actions

Corrida #4 del workflow «Evidencias del informe»: https://github.com/Ronald-Castillon/trucha-smart/actions/runs/43368473703

Cada página guarda el comando, su salida literal y el código de salida (0 = correcto). Las evidencias de calidad del producto se ejecutan sobre el tag v3.0-Inc3; las de despliegue y seguridad en ejecución, sobre main.

| Evidencia | Qué verifica | Versión | Código de salida |
|---|---|---|---|
| [x_ruff](x_ruff.md) | Linter ruff: estilo y formato | tag `v3.0-Inc3` @ `fdf2121` | 0 |
| [s_pytest](s_pytest.md) | Pruebas unitarias e integración con cobertura del dominio (M2.3) | tag `v3.0-Inc3` @ `fdf2121` | 0 |
| [r_salud](r_salud.md) | R · /api/salud responde 503 sin caerse cuando falla la base de datos | tag `v3.0-Inc3` @ `fdf2121` | 0 |
| [u_contraste](u_contraste.md) | U · Contraste de la paleta (WCAG 2.1 AA, 1.4.3) | tag `v3.0-Inc3` @ `fdf2121` | 0 |
| [u_axe](u_axe.md) | U · axe-core en las pantallas, móvil a 375 px y teclado | tag `v3.0-Inc3` @ `fdf2121` | 0 |
| [f_e2e_rf](f_e2e_rf.md) | F · Pruebas E2E de aceptación de cada requisito funcional | tag `v3.0-Inc3` @ `fdf2121` | 0 |
| [mas_bandit](mas_bandit.md) | + · SAST con Bandit (severidad media o alta) | tag `v3.0-Inc3` @ `fdf2121` | 0 |
| [mas_seguridad](mas_seguridad.md) | + · Pruebas de cabeceras, auditoría y configuración segura | tag `v3.0-Inc3` @ `fdf2121` | 0 |
| [mas_openapi](mas_openapi.md) | + · Contrato OpenAPI al día | tag `v3.0-Inc3` @ `fdf2121` | 0 |
| [g_m21](g_m21.md) | GQM M2.1 · capturas de aceptación en cada tag | rama `main` @ `f80fe18` | 0 |
| [g_m22](g_m22.md) | GQM M2.2 · defectos registrados por incremento | rama `main` @ `f80fe18` | 0 |
| [g_m31](g_m31.md) | GQM M3.1 · brechas AS-IS con capturas y casos de prueba | rama `main` @ `f80fe18` | 0 |
| [mas_pip_audit](mas_pip_audit.md) | + · pip-audit: vulnerabilidades conocidas en las dependencias (main) | rama `main` @ `f80fe18` | 0 |
| [dep_compose_build](dep_compose_build.md) | Despliegue · construcción de la imagen y arranque con docker compose | rama `main` @ `f80fe18` | 0 |
| [dep_compose_ps](dep_compose_ps.md) | Despliegue · contenedores en ejecución (aplicación y PostgreSQL 16) | rama `main` @ `f80fe18` | 0 |
| [dep_salud](dep_salud.md) | Despliegue · /api/salud y cabeceras de seguridad | rama `main` @ `f80fe18` | 0 |
| [dep_bd](dep_bd.md) | Despliegue · PostgreSQL 16 con los datos cargados | rama `main` @ `f80fe18` | 0 |
| [o_a01](o_a01.md) | OWASP A01:2025 contra la aplicación en Docker | rama `main` @ `f80fe18` | 0 |
| [o_a02](o_a02.md) | OWASP A02:2025 contra la aplicación en Docker | rama `main` @ `f80fe18` | 0 |
| [o_a04](o_a04.md) | OWASP A04:2025 contra la aplicación en Docker | rama `main` @ `f80fe18` | 0 |
| [o_a05](o_a05.md) | OWASP A05:2025 contra la aplicación en Docker | rama `main` @ `f80fe18` | 0 |
| [o_a07](o_a07.md) | OWASP A07:2025 contra la aplicación en Docker | rama `main` @ `f80fe18` | 0 |
| [o_a08](o_a08.md) | OWASP A08:2025 contra la aplicación en Docker | rama `main` @ `f80fe18` | 0 |
| [o_a09](o_a09.md) | OWASP A09:2025 contra la aplicación en Docker | rama `main` @ `f80fe18` | 0 |
| [o_a10](o_a10.md) | OWASP A10:2025 contra la aplicación en Docker | rama `main` @ `f80fe18` | 0 |
| [u_color](u_color.md) | U · WCAG 1.4.1: texto que acompaña a cada color de estado | rama `main` @ `f80fe18` | 0 |
| [u_aria_login](u_aria_login.md) | U · WCAG 4.1.2: árbol de accesibilidad de /login | rama `main` @ `f80fe18` | 0 |
| [u_aria_panel](u_aria_panel.md) | U · WCAG 4.1.2 y 2.4.1: árbol de accesibilidad del panel | rama `main` @ `f80fe18` | 0 |
| [dep_logs](dep_logs.md) | Despliegue · registro de peticiones del contenedor de la aplicación | rama `main` @ `f80fe18` | 0 |
| [ren_test](ren_test.md) | Render · pruebas automáticas del despliegue | rama `main` @ `f80fe18` | 0 |
| [ren_salud](ren_salud.md) | Render · /api/salud del sitio público y cabeceras | rama `main` @ `f80fe18` | 0 |
| [ren_https](ren_https.md) | Render · HTTP redirige a HTTPS y la cookie de sesión sale con Secure | rama `main` @ `f80fe18` | 0 |
| [ren_api](ren_api.md) | Render · API REST pública: login JWT, panel y riesgo del modelo de IA | rama `main` @ `f80fe18` | 0 |
