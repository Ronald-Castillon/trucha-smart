---
name: "Solicitud de Cambio (RFC)"
about: "Propuesta formal de modificación de requisitos, corrección o mejora"
title: "[RFC] "
labels: "change-request, pendiente-evaluacion"
---

<!-- Gestión de configuración (docs/scm/gestion_configuracion.md). Una RFC se aprueba cuando el
     Tech Lead cambia la etiqueta «pendiente-evaluacion» por «aprobado»; luego se implementa en una
     rama feature/* o hotfix/* y entra a develop por un Pull Request revisado. -->

### 1. DESCRIPCIÓN DEL CAMBIO SOLICITADO

- **Módulo / Componente Afectado:** [Ej. Módulo de Autenticación / API REST]
- **Tipo de Cambio:** Corrección de Defecto / Cambio de Requisito / Refactorización
- **Justificación:** [Explicar por qué el cambio genera valor a la organización]
- **Origen:** [Issue, prueba o medición que lo motiva]

### 2. ANÁLISIS DE IMPACTO

- **Impacto en Tiempo / Esfuerzo:** [Estimación en horas o Puntos de Historia]
- **Nivel de Riesgo:** [Bajo / Medio / Alto]
- **Elementos de configuración afectados:** [archivos, módulos, pruebas, documentación]
- **Línea base de destino:** [versión SemVer en la que se liberará, p. ej. v4.1.0]

### 3. CRITERIOS DE ACEPTACIÓN

- [ ] Pruebas unitarias actualizadas y ejecutadas sin errores.
- [ ] Pipeline de CI en verde en el Pull Request.
- [ ] Revisión de código aprobada por un par.
