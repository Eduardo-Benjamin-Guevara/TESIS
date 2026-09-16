# Sprint 9 — Despliegue en Vercel y temas visuales

## Objetivo

Llevar la aplicación a un **hosting permanente (24/7), gratuito y con
despliegue automático por `git push`**, independiente del lenguaje de la app
(Vercel). Además, corregir un problema visual en el panel de monitoreo y
ajustar de forma completa los colores de los temas **claro y oscuro** (tablas,
letras y tonalidades).

## Alcance

1. **Migración de hosting: Render → Vercel**
   - Entry point WSGI detectable automáticamente: `api/index.py` exporta `app`.
   - `vercel.json`: **sin rewrites** (Vercel detecta Flask y enruta cada petición a
     la función conservando el path original; reescribir `/` → `/api/index`
     rompía las rutas devolviendo 404). Solo define cabeceras de caché para
     estáticos.
   - Estáticos en `public/static/`: Vercel **no soporta `app.static_folder`** de
     Flask; los archivos deben estar en `public/` para servirse desde el CDN con
     el MIME correcto. Flask apunta `static_folder` a `public/static` para que
     en local la URL `/static/...` siga funcionando.
   - `.vercelignore`: excluye `venv/`, `instance/`, `backups/`, `.env`, etc.
   - **PostgreSQL persistente**: serverless = filesystem efímero, por lo que
     SQLite no sirve. Se añadió `psycopg2-binary` y soporte de `DATABASE_URL`
     en `config.py` (con prioridad sobre `SQLALCHEMY_DATABASE_URI`).
   - **Siembra tolerante a concurrencia**: varios cold starts importan la app en
     paralelo y competían por insertar el usuario `demo` (UniqueViolation).
     `inicializar_bd` ahora reintenta hasta 4 veces ante `IntegrityError`
     (rollback + re-verificación), quedando idempotente en serverless.
   - Tolerancia a filesystem de solo lectura: `os.makedirs` en `config.py` y
     en la fábrica (`app/__init__.py`) ahora se protegen con `try/except`.
   - El arranque es idempotente: crea tablas, admin y datos demo en una base
     PostgreSQL nueva (funciona igual que con SQLite local).
   - QR y exportaciones usan `BytesIO` (memoria), compatibles con serverless.

2. **Fix panel de monitoreo (área blanca fuera de lugar)**
   - `dashboard.html`: se eliminó un `</div>` extra que rompía el layout
     (causaba una zona en blanco sin relación con el diseño).
   - Los 3 gráficos (stock por categoría, estado de inventario y movimientos)
     ahora se dibujan con colores de ejes/leyendas según el tema activo.

3. **Colores de temas claro y oscuro (tablas, letras, tonalidades)**
   - `app.css`: se reescribió la sección del tema oscuro cubriendo totalmente
     tablas (incluidas filas `table-warning`, celdas, encabezados), badges
     `*-subtle`, alerts, botones outline, dropdowns, modales y formularios
     (`form-control`, `form-select`, `input-group-text`).
   - `auth.css`: modo oscuro para login y páginas de error (antes no existía).
   - `login.html` y `errors/base_error.html`: script inline que aplica el tema
     guardado en `localStorage` antes del primer render (evita parpadeo).
   - `app.js`: se emite un evento `tema:cambio` al alternar tema.
   - `dashboard.html`: escucha `tema:cambio` y redibuja los gráficos de
     Chart.js al instante (sin recargar la página).

## Archivos modificados o creados

| Archivo | Cambio |
|---|---|
| `api/index.py` | **Nuevo**: entry point WSGI (`app`) para Vercel |
| `vercel.json` | **Nuevo**: cabeceras de caché para estáticos (sin rewrites) |
| `.vercelignore` | **Nuevo**: excluye archivos locales del bundle |
| `requirements.txt` | Añade `psycopg2-binary` para PostgreSQL |
| `app/config.py` | Soporta `DATABASE_URL`, `makedirs` tolerante a solo lectura |
| `app/__init__.py` | `makedirs` protegido (serverless) + siembra con reintento por `IntegrityError` |
| `app/static/css/app.css` → `public/static/css/app.css` | Tema oscuro completo (tablas, forms, badges, alerts, modales) |
| `app/static/css/auth.css` → `public/static/css/auth.css` | Modo oscuro para login/errores |
| `app/static/js/app.js` → `public/static/js/app.js` | Evento `tema:cambio` |
| `app/templates/auth/login.html` | Script inline de tema + loader |
| `app/templates/errors/base_error.html` | Script inline de tema |
| `app/templates/monitoreo/dashboard.html` | Fix `</div>` extra + gráficos theme-aware |
| `.env.example` | Documenta `DATABASE_URL` |
| `README.md` | Sección de despliegue en Vercel + fila de sprint |

## Pasos de despliegue (Vercel)

1. Crear base PostgreSQL en Neon (plan gratuito).
2. Importar el repo en Vercel y definir las variables de entorno de
   producción (`FLASK_CONFIG=production`, `SECRET_KEY`, `DATABASE_URL`,
   `ADMIN_USUARIO`, `ADMIN_PASSWORD`, `ANALYTICS_TAG` opcional).
3. El primer despliegue crea tablas, admin y datos demo automáticamente.
4. A partir de entonces, cada `git push` actualiza la producción.

## Verificación

- **107/107 pruebas automatizadas pasan** (`python -m pytest`), incluida una
  prueba nueva que simula la colisión de concurrencia en el sembrado.
- La app importa correctamente a través del entry point de Vercel
  (`from api.index import app`, 41 rutas registradas).
- Los estáticos se sirven al arrancar localmente (`/static/css/app.css` →
  `200 text/css`) y en Vercel desde `public/` por el CDN.
- Los gráficos se redibujan al alternar el tema; no hay áreas blancas
  huérfanas en el dashboard.