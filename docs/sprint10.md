# Sprint 10 — Diagrama de arquitectura y documentación de pruebas

## Objetivo

Entregar el **diagrama de arquitectura del sistema** en formato XML (editables
para el documento de tesis) y la **documentación de las pruebas aplicadas** al
sistema, solicitados para la presentación del capítulo correspondiente.

## Entregables

1. **`docs/diagrama_arquitectura.drawio`** — diagrama en **XML de draw.io**
   (diagrams.net), abierto directamente en <https://app.diagrams.net> y
   exportable a PNG/SVG/PDF. Contiene dos páginas:

   - **Página 1 — Arquitectura del sistema**:
     - Cliente (navegador: HTML5, CSS3, JavaScript, Bootstrap 5, Jinja2,
       Chart.js).
     - Plataforma **Vercel** (serverless): entry point `api/index.py` (WSGI),
       fábrica `create_app()`, capa de **blueprints/rutas** (10 módulos),
       capa de **servicios** (15 servicios de lógica de negocio), capa de
       **modelos** (SQLAlchemy: 6 entidades), **extensiones** (SQLAlchemy,
       Flask-Migrate, Flask-WTF/CSRF, Flask-Login) y **estáticos por CDN**
       (`public/static`).
     - **Base de datos**: PostgreSQL (Neon) en producción, SQLite en
       desarrollo — conexión por `DATABASE_URL`.
   - **Página 2 — Pruebas automatizadas**:
     - Flujo de ejecución de pruebas: cliente de prueba → rutas/blueprints →
       servicios → ORM → SQLite en memoria aislada.
     - 10 módulos de pruebas con sus casos, y total **107/107 aprobadas
       (100%)**.

2. **`reporte_tests.html`** regenerado con **107/107 (100%)** — evidencia de las
   pruebas aplicadas, con captura de consola por cada caso.

3. **README** — nueva sección "Arquitectura del sistema y pruebas aplicadas"
   que resume el diagrama, la tabla de módulos de pruebas y cómo regenerar el
   reporte; se documentó como **Sprint 10**.

## Verificación

- `python -m pytest` → **107 passed**.
- `python generar_reportes.py` → `RESUMEN: 107 aprobadas | 0 fallidas | 100%`.
- El XML del diagrama se valida correctamente (2 diagramas: "Arquitectura del
  sistema" y "Pruebas automatizadas").