# Sprint 8 – Pulido profesional (SEO, seguridad, copias de seguridad y rendimiento)

**Rama:** `sprint/8`
**Estado:** Completado

## Alcance

Este sprint convierte la aplicación en un producto listo para producción y
presentación ante un jurado, añadiendo mejoras en seis frentes:

1. **SEO básico**: meta descripción, Open Graph, favicon, `robots.txt` y
   `sitemap.xml`.
2. **Seguridad**: cabeceras HTTP de protección, bloqueo por fuerza bruta en el
   login y mensajes de error controlados.
3. **Copias de seguridad**: comandos CLI para crear y listar respaldos de la
   base de datos SQLite.
4. **Manejo de errores**: páginas 403/404/500 rediseñadas y con copywriting
   claro.
5. **Rendimiento**: caché de estáticos (`SEND_FILE_MAX_AGE_DEFAULT`),
   *preconnect* a CDNs, fuente Nunito cargada con `display=swap` y assets con
   *cache-busting* (`?v=5`).
6. **UX / Accesibilidad / Consola**: *loading states* (spinners) en
   formularios, foco visible para teclado, `prefers-reduced-motion`, corrección
   de un error de consola y alt/ARIA en iconos.

## Módulos y cambios

### SEO (`base.html`, `config.py`, `main.py`)

- **Cabeza de documento**: `description`, Open Graph (título, descripción,
  url, tipo), Twitter Card, `canonical`, favicon SVG y block de metadatos por
  página (`{% block head %}`).
- **`GET /robots.txt`**: permite a todos los rastreadores y apunta al sitemap.
- **`GET /sitemap.xml`**: lista las rutas públicas principales
  (`/`, `/login`, `/alimentos/`, alertas, reportes, etc.).
- **`app/static/favicon.svg`**: nuevo icono de marca (SVG, vectorial).
- Se mantiene el *cache-busting* `?v=5` para `app.css` y `app.js`.

### Seguridad

- **Cabeceras HTTP** (`after_request` en `app/__init__.py`):
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: SAMEORIGIN` (evita clickjacking)
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - `Permissions-Policy` (restringe cámara, micrófono, geolocalización)
  - `Strict-Transport-Security` (HSTS) **solo en producción**.
- **Protección contra fuerza bruta** (`auth.py`): tras **5 intentos fallidos**
  de login se bloquea el acceso durante **5 minutos** (usando la sesión).
- Los mensajes de error no revelan detalles internos.

### Copias de seguridad (`backup_service` + CLI)

- `flask --app run.py backup` → copia la BD a `backups/sistema_alimentos_AAAAMMDD_HHMMSS.db`.
- `flask --app run.py backup -o ruta` → permite elegir destino.
- `flask --app run.py backup-list` → lista respaldos (archivo, fecha, tamaño).
- Antes de copiar se limpia la sesión (`db.session.remove()`) para que el
  archivo quede consistente.

### Manejo de errores (`base_error.html` + `__init__.py`)

- Plantilla única para 403/404/500 con código grande, icono, mensaje claro y
  dos acciones: **"Ir al panel"** y **"Volver atrás"**.
- Copywriting en español claro y sin tecnicismos.
- `robots: noindex, nofollow` en páginas de error.

### Rendimiento

- `SEND_FILE_MAX_AGE_DEFAULT = 7 días` para que el navegador cachee
  CSS/JS/imágenes sin revalidar.
- `preconnect` a `cdn.jsdelivr.net` y `fonts.googleapis.com` en la cabeza.
- Fuente **Nunito** con `display=swap` (no bloquea el render).
- Assets `app.css`/`app.js` con `?v=5`.

### UX / Accesibilidad / Consola

- **Loading state automático**: al enviar cualquier formulario, el botón
  submit se deshabilita y muestra un *spinner* + texto (evita dobles envíos).
  Se puede desactivar por botón con `data-no-loading`.
- **Login**: spinner "Ingresando..." al enviar, `autocomplete` correcto y
  mensaje de bloqueo temporal.
- **Foco visible** (`:focus-visible`) para navegación por teclado.
- **`prefers-reduced-motion`**: se minimizan animaciones/transiciones para
  quienes lo prefieran.
- **Corrección de consola**: se definían `notifWrap` y `userMenu` de forma
  incorrecta en `app.js` (la variable `userMenu` se usaba antes de existir);
  se corrigieron para que el cierre de menús funcione sin errores JS.
- Los iconos decorativos tienen `aria-hidden="true"` (el sistema usa iconos
  vectoriales, no `<img>`).

## Pruebas funcionales

Nuevo archivo `tests/test_profesionalismo.py`.

- **95 → 106 pruebas**, todas pasando.
- Cobertura:
  - `robots.txt` y `sitemap.xml` responden 200 con contenido correcto.
  - `/health` devuelve `{"estado": "ok"}`.
  - Cabeceras de seguridad presentes en todas las respuestas.
  - Página 404 muestra contenido amigable y no exige login.
  - `favicon.svg` accesible como SVG.
  - Bloqueo por fuerza bruta: tras 5 intentos fallidos se avisa del bloqueo.
  - Un login correcto limpia el contador de intentos.
  - Comando `backup` crea un respaldo legible (con BD simulada en test).

## Verificación de requerimientos (lista del usuario)

- [x] **SEO básico** (titulos, meta description, canonical, Open Graph).
- [x] **Sitemap.xml** y **robots.txt**.
- [x] **Favicon**.
- [x] **Analytics** (Google Analytics opt-in vía `ANALYTICS_TAG` en entorno).
- [x] **Seguridad** (cabeceras, bloqueo de fuerza bruta, secretos en `.env`).
- [x] **Copias de seguridad** (CLI `backup` / `backup-list`).
- [x] **Manejo de errores** (403/404/500 con diseño y copywriting).
- [x] **Loading states** en formularios y login.
- [x] **Consola sin errores** (corregido `userMenu`/`notifWrap`).
- [x] **Accesibilidad** (foco visible, ARIA, `prefers-reduced-motion`).
- [x] **Rendimiento** (etiquetas de caché, preconnect, `display=swap`).
- [x] **Links OK** (enlaces internos verificados contra rutas reales).
- [x] **Imágenes / alt text** (sistema 100% de iconos vectoriales con ARIA).

## Errores identificados y corregidos

1. **Emoji roto en CLI**: `✅` no se codifica en terminales Windows (cp1252);
   se reemplazó por `[OK]`.
2. **Error de consola JS**: las variables `notifWrap`/`userMenu` se usaban sin
   estar definidas en `app.js`; se corrigió su declaración.
3. **Botón submit bloqueado permanentemente**: el *loading state* ahora sólo
   actúa sobre el envío y respeta `data-no-loading` (p. ej. "Volver atrás").

## Evaluación del incremento

El Sprint 8 deja la aplicación con apariencia y comportamiento de **producto
final**: óptima para el buscador, protegida ante ataques comunes, respaldable
en un clic, rápida de cargar y sin mensajes de error confusos — justo lo que se
espera de una tesis al presentarse ante un jurado.

## Siguiente paso

Juntar `sprint/1` a `sprint/8` en `main`, consolidar la documentación global y
crear el manual de usuario/informe final de la tesis.