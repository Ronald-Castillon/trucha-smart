# ADR-008: Despliegue público en Render con la imagen Docker y PostgreSQL gestionado

- **Estado:** Aceptado
- **Fecha:** 2026-11-12
- **Relacionado:** ADR-003 (persistencia detrás de un puerto), restricción de despliegue en contenedores

## Contexto
El curso exige que la web esté desplegada y accesible. TruchaSmart es una aplicación FastAPI de
proceso largo: el sensor simulado del panel corre en hilos dentro del mismo proceso y la base de
producción es PostgreSQL. Se evaluó Vercel: ejecuta Python como funciones serverless que se apagan
entre peticiones, por lo que el sensor simulado no funcionaría, y no ofrece PostgreSQL propio.

## Decisión
Desplegar en **Render** con un *Blueprint* (`render.yaml`) que crea:
- un servicio web que construye la **misma imagen Docker** del repositorio (sin un empaquetado
  distinto para producción) y se vuelve a desplegar en cada push a `main`;
- una base **PostgreSQL 16** gestionada, cuya cadena de conexión se inyecta en `DATABASE_URL`.

La imagen escucha en el puerto de la variable `PORT`, normaliza la URL `postgresql://` del
proveedor al controlador psycopg y, al arrancar, ejecuta `tools/init_db.py --si-vacia` para crear el
esquema y los datos demo solo si la base está vacía. `APP_ENV=produccion` y `JWT_SECRET` generado por
Render activan las protecciones de producción (clave propia, cookie `Secure`).

## Consecuencias
- (+) Todo el producto funciona en la nube, incluido el panel en vivo con el sensor simulado.
- (+) Producción usa exactamente la imagen probada en CI (job `docker`).
- (−) Plan gratuito: el servicio se duerme tras 15 min sin tráfico (la primera visita tarda ~1 min)
  y la base gratuita de Render caduca a los 30 días si no se pasa a un plan pago.
- (−) Los usuarios demo con contraseñas publicadas en el README quedan accesibles en un sitio
  público: deben cambiarse si el sistema se usa con datos reales.
