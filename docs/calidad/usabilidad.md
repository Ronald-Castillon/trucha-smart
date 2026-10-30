# Usabilidad (FURPS+ U): psicología del color y accesibilidad WCAG 2.1 AA

Issue #30 (RNF-U) · defecto encontrado y corregido: #36 · Incremento 3

## 1. Paleta por dominio y su justificación

| Rol | Color | Justificación (psicología del color en el dominio acuícola) |
|---|---|---|
| Primario (menú, botones) | `#0b6e8a` azul petróleo | Asociado al agua y a la calma; transmite confianza y estabilidad en una herramienta de monitoreo que se consulta todo el día. |
| Fondo / superficie | `#f4f7f9` / `#ffffff` | Neutros fríos y claros: no compiten con los colores de estado y reducen la fatiga visual. |
| Texto | `#1d2b36` | Azul casi negro: máximo contraste (13–14:1) sin la dureza del negro puro. |
| Normal | `#17773f` verde | Convención universal de "todo bien"; tono profundo para que el texto blanco sea legible. |
| Precaución | `#f2c94c` ámbar con texto oscuro; `#8a6100` para texto | El amarillo/ámbar llama la atención sin alarmar: "revisar pronto". Se usa como relleno con texto oscuro porque el texto blanco sobre ámbar no es legible. |
| Crítica | `#c0392b` rojo | Urgencia y peligro (hipoxia, temperatura letal): exige acción inmediata. Se reserva para riesgos reales, para no generar fatiga de alarmas. |

El color **nunca es el único indicador** (WCAG 1.4.1): cada nivel también se escribe en texto
("NORMAL", "PRECAUCION", "CRITICA"), el riesgo muestra su valor numérico y los avisos tienen título.

## 2. Contraste de la paleta (WCAG 1.4.3)

Calculado con `python tools/contraste_paleta.py --markdown` (luminancia relativa de WCAG). El paso
"Contraste de la paleta" del job de calidad en CI falla si algún par baja de 4.5:1.

| Texto | Fondo | Contraste | AA (≥ 4.5:1) | Uso |
|---|---|---:|:---:|---|
| texto `#1d2b36` | fondo `#f4f7f9` | 13.45:1 | Sí | texto general sobre el fondo de la página |
| texto `#1d2b36` | superficie `#ffffff` | 14.47:1 | Sí | texto en tarjetas |
| suave `#5b6b78` | superficie `#ffffff` | 5.50:1 | Sí | texto secundario (.suave, etiquetas de formulario) |
| suave `#5b6b78` | fondo `#f4f7f9` | 5.11:1 | Sí | texto secundario fuera de tarjetas |
| #ffffff `#ffffff` | primario `#0b6e8a` | 5.81:1 | Sí | menú superior y botones |
| primario `#0b6e8a` | superficie `#ffffff` | 5.81:1 | Sí | botón secundario y enlaces |
| #ffffff `#ffffff` | verde `#17773f` | 5.60:1 | Sí | etiqueta / semáforo NORMAL |
| texto `#1d2b36` | amarillo `#f2c94c` | 9.12:1 | Sí | etiqueta / semáforo PRECAUCIÓN (texto oscuro) |
| #ffffff `#ffffff` | rojo `#c0392b` | 5.44:1 | Sí | etiqueta / semáforo CRÍTICA, botón detener simulador |
| amarillo-texto `#8a6100` | superficie `#ffffff` | 5.54:1 | Sí | valor en nivel de precaución (.nivel-PRECAUCION) |
| rojo `#c0392b` | superficie `#ffffff` | 5.44:1 | Sí | valor crítico, predicción de riesgo, bitácora |
| verde `#17773f` | superficie `#ffffff` | 5.60:1 | Sí | indicador 'en vivo' |
| rojo `#c0392b` | #fdecea `#fdecea` | 4.76:1 | Sí | mensaje de error |
| verde `#17773f` | #e8f5ee `#e8f5ee` | 5.00:1 | Sí | mensaje de confirmación |

## 3. Auditoría automatizada con axe-core

`tests/e2e/test_accesibilidad_axe.py` inyecta **axe-core 4.12.1** en las 12 pantallas (como
Administrador, con los datos demo) y ejecuta las reglas etiquetadas `wcag2a`, `wcag2aa`,
`wcag21a`, `wcag21aa`. La prueba falla con cualquier violación y deja el resultado de cada
ejecución en `evidencias/inc3/axe/resumen.md` y `resultados.json`.

| Ejecución | Violaciones | Pantallas con violaciones | Evidencia |
|---|---:|---:|---|
| Primera (paleta del Inc2) | 4 (`color-contrast`, serious) | 4 de 12 | `evidencias/inc3/axe/resumen_inicial_antes_de_corregir.md` |
| Tras corregir la paleta (#36) | **0** | 0 de 12 | `evidencias/inc3/axe/resumen.md` |

## 4. Teclado y foco (WCAG 2.1.1, 2.4.1, 2.4.7)

- Enlace **"Saltar al contenido"** como primer elemento enfocable de cada página.
- Foco visible en todos los controles (`:focus-visible`: contorno ámbar con halo oscuro, legible
  sobre fondos claros y sobre el menú azul).
- Verificado por `test_teclado_saltar_al_contenido_y_foco_visible` (Tab → enlace visible → Enter
  lleva el foco a `<main id="contenido">`).

## 5. Límites de esta verificación

axe-core detecta automáticamente alrededor de un tercio a la mitad de los problemas de WCAG; no
sustituye una revisión manual con lector de pantalla ni pruebas con usuarios reales de la
piscigranja. Esas pruebas quedan como trabajo del equipo.
