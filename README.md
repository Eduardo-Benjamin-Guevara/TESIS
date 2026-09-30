# Sistema Web Inteligente para la Gestión y Control de Alimentos

**I.E.I. N.° 1488** — Proyecto de tesis para el grado de bachiller en
Ingeniería de Sistemas Computacionales.

> **Versión 1** — Base funcional del sistema (arquitectura, base de datos,
> autenticación, gestión de usuarios y CRUD de alimentos).

---

## Descripción del proyecto

El sistema es una aplicación web desarrollada en **Python (Flask)** orientada a
la gestión de alimentos de la I.E.I. N.° 1488. Busca resolver los problemas de:

- Registro manual y disperso de alimentos.
- Falta de control del inventario.
- Pérdidas por vencimiento.
- Dificultad para consultar la información.
- Falta de reportes.

Esta primera versión sienta las bases: arquitectura modular, base de datos
gestionada con migraciones, autenticación segura por roles y el CRUD completo
de alimentos, todo con una interfaz web profesional y responsive.

---

## Objetivo

Construir la **base funcional** del sistema preparada para crecer: una
arquitectura limpia y extensible que, en versiones posteriores, incorporará
lotes, fechas de vencimiento y alertas, proveedores, entradas/salidas,
fotografías, códigos QR, trazabilidad, tableros (dashboard) y reportes.

---

## Tecnologías

| Tecnología | Uso |
|---|---|
| Python 3.12+ | Lenguaje de programación |
| Flask 3 | Framework web |
| Flask-SQLAlchemy | ORM / modelos |
| Flask-Migrate (Alembic) | Migraciones de base de datos |
| Flask-Login | Manejo de sesiones y autenticación |
| Flask-WTF / WTForms | Formularios y protección CSRF |
| Werkzeug | Hash seguro de contraseñas |
| SQLite | Base de datos de desarrollo |
| Jinja2 | Motor de plantillas |
| HTML5 / CSS3 / JavaScript | Frontend |
| Bootstrap 5 | Marco de estilos y componentes |
| Pytest | Pruebas automatizadas |

La arquitectura está preparada para **migrar de SQLite a PostgreSQL en
producción** sin reescribir el sistema: basta con cambiar la variable
`SQLALCHEMY_DATABASE_URI` en `.env` (los modelos usan tipos portables y las
migraciones son independientes del motor).

---

## Arquitectura

El proyecto usa un **patrón de fábrica de aplicación (application factory)**
combinado con una **arquitectura en capas**:

- **routes/** — Capa de presentación (blueprints). Recibe la petición HTTP y
  delega la lógica de negocio a los servicios. Delgada y sin reglas de dominio.
- **services/** — Capa de lógica de negocio. Contiene las reglas del dominio
  (validaciones de código único, categorías válidas, etc.) independientes de
  Flask. Facilita las pruebas.
- **models/** — Capa de datos. Definición de las entidades (tablas) con
  SQLAlchemy.
- **templates/** y **static/** — Capa de presentación (Jinja2 + Bootstrap).

Esta separación mantiene **rutas delgadas, lógica reutilizable y modelos
desacoplados**, de modo que añadir funcionalidades en versiones futuras no
obligue a reescribir el código existente.

### Justificación de la estructura

Respecto al esquema propuesto, se mantiene casi por completo. Se añadió el
módulo **`app/cli.py`** para comandos administrativos (`flask init-db`,
`flask create-admin`) y se usa `instance/` para la base de datos local, que
queda fuera del control de versiones. La creación del administrador inicial y
la aplicación de migraciones se manejan mediante comandos explícitos en lugar
de ejecutarse automáticamente en cada arranque, lo que es más seguro,
predecible y adecuado para pasar a producción.

```
project/
├── app/
│   ├── __init__.py        # Fábrica de aplicación
│   ├── config.py          # Configuración por entorno
│   ├── extensions.py      # Extensiones Flask (db, migrate, csrf)
│   ├── cli.py             # Comandos FLask CLI
│   ├── models/
│   │   ├── __init__.py
│   │   ├── usuario.py     # Entidad Usuario
│   │   └── alimento.py    # Entidad Alimento
│   ├── routes/
│   │   ├── auth.py        # Login / logout
│   │   ├── main.py        # Panel principal
│   │   ├── alimentos.py   # CRUD de alimentos
│   │   └── usuarios.py    # Administración de usuarios
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── alimento_service.py
│   │   └── init_services.py
│   ├── templates/         # Vistas Jinja2
│   ├── static/            # (movido a public/static para Vercel)
│   └── utils/
│       ├── decorators.py  # Protección de rutas por rol
│       └── security.py
├── migrations/            # Migraciones Alembic
├── tests/                 # Pruebas automatizadas
├── instance/              # Base de datos local (no versionada)
├── .env                   # Variables de entorno (no versionado)
├── .env.example
├── .gitignore
├── requirements.txt
├── pytest.ini
├── run.py
└── README.md
```

### Base de datos

Entidades iniciales:

**Usuario** — `id`, `nombre`, `usuario` (único), `password_hash`, `rol`,
`activo`, `fecha_creacion`, `ultima_sesion`.

**Alimento** — `id`, `codigo` (único), `nombre`, `categoria`,
`unidad_medida`, `descripcion`, `stock_actual`, `stock_minimo`, `activo` (baja
lógica), `fecha_creacion`, `fecha_actualizacion`.

- La **eliminación es lógica** (flag `activo`); no se borran registros.
- El campo `activo` de Alimento permite ocultar/archivar alimentos sin perder
  su historial, preparando el terreno para trazabilidad en V2.
- El diseño queda listo para incorporar en V2: **lotes, fechas de vencimiento,
  proveedores, entradas/salidas, responsables, fotografías y códigos QR**.

---

## Funcionalidades implementadas (V1)

- **Autenticación**: login, logout, sesiones (Flask-Login) y contraseñas con
  hash seguro (Werkzeug). Bloqueo temporal tras 5 intentos fallidos.
- **Protección de rutas**: acceso restringido por autenticación y por rol
  (admin / encargado / consulta) mediante decoradores.
- **Gestión de usuarios** (solo admin): crear usuarios, activar/desactivar
  cuentas y asignar roles.
- **CRUD de alimentos**:
  - Registrar alimento (código único, validación de campos obligatorios).
  - Editar alimento (revalida código único excluyendo el propio).
  - Consultar detalle de un alimento.
  - Buscar por código o nombre.
  - Filtrar por categoría.
  - Activar/desactivar (baja lógica).
- **Panel principal** con resumen: total de alimentos y stock bajo.
- **Interfaz profesional responsive** con sidebar colapsable, barra superior,
  formularios, tablas, mensajes flash y páginas de error (403/404/500).
- **Loading states** en formularios (spinner en el botón de envío).
- **Seguridad**: hash de contraseñas, CSRF, variables sensibles en `.env`,
  cabeceras HTTP de protección (X-Content-Type-Options, X-Frame-Options,
  Referrer-Policy, Permissions-Policy), uso del ORM (sin SQL inyección) y
  mensajes de error controlados.
- **Copias de seguridad**: comandos CLI (`flask backup` y
  `flask backup-list`) para crear y listar respaldos de la base de datos.
- **SEO básico**: meta descripción, Open Graph, canonical, favicon SVG,
  `robots.txt` y `sitemap.xml`.
- **Rendimiento**: caché de estáticos (7 días), preconnect a CDNs, fuente
  Nunito con `display=swap`, *cache-busting* en assets.
- **Accesibilidad**: foco visible, atributos ARIA, `prefers-reduced-motion`.
- **Datos de demostración**: 26 alimentos, 28 lotes y 53 movimientos
  sembrados desde el panel o CLI (`flask seed-demo`).

---

## Instalación

Requisitos: Python 3.12+.

1. Clonar o copiar el proyecto.
2. Crear un entorno virtual:

   ```bash
   python -m venv venv
   ```

3. Activar el entorno:

   - Windows (PowerShell):

     ```powershell
     .\venv\Scripts\Activate.ps1
     ```

   - Windows (CMD):

     ```cmd
     venv\Scripts\activate.bat
     ```

   - Linux / macOS:

     ```bash
     source venv/bin/activate
     ```

4. Instalar las dependencias:

   ```bash
   pip install -r requirements.txt
   ```

5. Instalar la herramienta de pruebas:

   ```bash
   pip install pytest
   ```

---

## Configuración

1. Copiar `.env.example` a `.env`:

   - Windows: `copy .env.example .env`
   - Linux/macOS: `cp .env.example .env`

2. Editar `.env` y ajustar, al menos:

   - `SECRET_KEY`: clave secreta aleatoria.
   - `ADMIN_PASSWORD`: contraseña del administrador inicial.

   Para generar una `SECRET_KEY`:

   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

> **Nunca** subir `.env` al repositorio (ya está en `.gitignore`).

---

## Despliegue en Vercel (producción, 24/7)

La aplicación está lista para desplegarse en **Vercel** de forma gratuita y
**sin configuración manual**: Vercel detecta automáticamente la instancia WSGI
`app` en `api/index.py` y la convierte en una Vercel Function (Fluid compute).
Cada `git push` a `main` genera un nuevo despliegue de producción.

### Base de datos (PostgreSQL gratuito con Neon)

Vercel ejecuta funciones serverless con un sistema de archivos efímero, por lo
que **SQLite no es persistente**. Para producción se usa **PostgreSQL**:
`config.py` soporta la variable `DATABASE_URL` y las tablas/datos iniciales se
crean automáticamente al primer arranque (idempotente). En el código se añadió
`psycopg2-binary` para conectar con PostgreSQL.

Pasos:

1. Crear un proyecto en <https://neon.tech> (plan gratuito) y copiar su cadena
   de conexión (formato `postgresql://usuario:password@host/db?sslmode=require`).
2. En Vercel (<https://vercel.com>), importar este repositorio de GitHub y
   añadir las variables de entorno en **Settings → Environment Variables**:
   - `FLASK_CONFIG=production`
   - `SECRET_KEY=<clave aleatoria>` (genérala con
     `python -c "import secrets; print(secrets.token_hex(32))"`)
   - `DATABASE_URL=<cadena de Neon>`
   - `ADMIN_USUARIO=admin`, `ADMIN_PASSWORD=<clave fuerte>`
   - `CREATE_ADMIN_ON_START=true` (crea el admin al primer arranque)
   - `ANALYTICS_TAG=<id de Google Analytics>` (opcional)
3. Vercel construye el proyecto en cada `push` (Python runtime). No se usa
   build command: la detección es automática (`vercel.json` solo define
   rewrites a `api/index` y caché de estáticos de 7 días).
4. El primer arranque crea tablas, el administrador y datos de demostración.
   La primera petición tras un *cold start* puede tardar unos segundos.

> La cookie de sesión se marca como segura (HTTPS) automáticamente en
> producción. Nunca fijes `SQLALCHEMY_DATABASE_URI` a SQLite en Vercel.

Archivos involucrados: `api/index.py`, `vercel.json`, `.vercelignore`,
`requirements.txt` (con `psycopg2-binary`).

---

## Ejecución

Con el entorno activo y desde la raíz del proyecto:

1. **Inicializar la base de datos** (aplica migraciones y crea el
   administrador inicial):

   ```bash
   flask --app run.py init-db
   ```

2. **Iniciar la aplicación**:

   ```bash
   python run.py
   ```

   La aplicación estará disponible en <http://127.0.0.1:5000>.

En lugar de `init-db` también puedes usar, por separado:

```bash
flask --app run.py db upgrade   # aplica migraciones
flask --app run.py create-admin # crea el administrador desde .env
```

---

## Usuario inicial

Tras ejecutar `init-db` se crea un administrador con los valores definidos en
`.env` (por defecto):

| Campo | Valor predeterminado |
|---|---|
| Usuario | `admin` |
| Contraseña | `admin123` |
| Rol | `admin` |

> **Importante:** cambia la contraseña en `.env` antes de usar el sistema en
> un entorno compartido o de producción.

---

## Roles del sistema

| Rol | Permisos |
|---|---|
| `admin` | Acceso total (alimentos, usuarios, activar/desactivar) |
| `encargado` | Registrar y editar alimentos, consultar |
| `consulta` | Solo consultar (sin editar) |

---

## Cómo ejecutar las pruebas

Con el entorno activo:

```bash
python -m pytest
```

Las pruebas cubren:

- Inicio de sesión (éxito, fallo, cuenta inactiva, logout, redirección).
- Registro de alimento.
- Edición de alimento.
- Consulta de alimento.
- Búsqueda y filtrado.
- Validación de código duplicado.
- Validación de campos obligatorios.
- Acceso no autorizado (rutas protegidas) y control por rol.

---

## Hoja de ruta (sprints)

El proyecto se desarrolla por sprints, cada uno en su propia rama de Git y
documentado en `docs/sprintN.md`.

| Sprint | Rama | Alcance | Estado |
|---|---|---|---|
| 1 | `sprint/1` | Registro y control de alimentos (usuarios, alimentos, categorías, fechas de vencimiento, consulta) | ✅ Completado |
| 2 | `sprint/2` | Gestión de inventario (entradas, salidas, actualización de stock, disponibilidad, historial) | ✅ Completado |
| 3 | `sprint/3` | Sistema de alertas (próximos a vencer, stock bajo, notificaciones, priorización) | ✅ Completado |
| 4 | `sprint/4` | Monitoreo y reportes (dashboard, entradas/salidas, stock en tiempo real, reportes, indicadores) | ✅ Completado |
| 5 | `sprint/5` | Funciones innovadoras (gráficos, QR, exportar reportes, recomendaciones, trazabilidad) | ✅ Completado |
| 6 | `sprint/6` | Usabilidad y profesionalismo (notificaciones funcionales, tema claro/oscuro, responsive y extras) | ✅ Completado |
| 7 | `sprint/7` | Datos de simulación (alimentos, lotes, movimientos demo; carga por CLI y panel) | ✅ Completado |
| 8 | `sprint/8` | Pulido profesional (SEO, seguridad, copias de seguridad, errores 403/404/500, rendimiento, UX y accesibilidad) | ✅ Completado |
| 9 | `sprint/9` | Deploy en Vercel 24/7 con PostgreSQL (Neon), paneles con gráficos adaptables al tema y ajuste global de colores claro/oscuro | ✅ Completado |
| 10 | `sprint/10` | Diagrama de arquitectura del sistema (XML draw.io) y documentación de pruebas aplicadas | ✅ Completado |

Cada sprint incluye: **pruebas funcionales, verificación de requerimientos,
identificación y corrección de errores, y evaluación del incremento**.

Para consultar el detalle de cada sprint: `docs/sprintN.md`.

Se contempla también la migración a **PostgreSQL** en producción (la
arquitectura ya está preparada para ello).


---

## Arquitectura del sistema y pruebas aplicadas (Sprint 10)

### Diagrama de arquitectura (XML)

El diagrama de arquitectura del sistema está disponible en formato **XML de
draw.io** (se abre directamente en <https://app.diagrams.net> y se puede
exportar a imagen/PDF para el documento de tesis):

- **`docs/diagrama_arquitectura.drawio`** — diagrama XML editable (draw.io,
  abrir en https://app.diagrams.net).
- **`docs/diagrama_en_texto.md`** — descripción caja por caja para recrear el
  diagrama en cualquier herramienta (draw.io, Lucidchart, Word, PowerPoint).

Ambos contienen **2 partes**: (1) la arquitectura del sistema y (2) las
pruebas aplicadas.

### Pruebas aplicadas

El sistema cuenta con una **suíte automatizada de 107 pruebas** (Pytest) que
cubre las cuatro capas de la aplicación. Al ejecutarlas se usa una base de
datos en memoria aislada para cada prueba.

| Módulo de pruebas | Pruebas | Cobertura |
|---|---|---|
| `test_acceso.py` | 7 | Rutas protegidas y control por rol |
| `test_auth.py` | 6 | Login, logout y bloqueo por intentos |
| `test_alimentos.py` | 11 | CRUD de alimentos, validaciones, búsqueda y filtros |
| `test_alertas.py` | 11 | Vencen pronto, stock bajo y prioridades |
| `test_inventario.py` | 12 | Entradas, salidas y actualización de stock |
| `test_innovacion.py` | 15 | QR, exportación, recomendaciones y trazabilidad |
| `test_monitoreo.py` | 9 | Dashboard, reportes e indicadores |
| `test_notificaciones.py` | 11 | Notificaciones y marcado de leídas |
| `test_profesionalismo.py` | 11 | SEO, seguridad, errores, backups y concurrencia serverless |
| `test_simulacion.py` | 14 | Generación de datos de simulación |
| **Total** | **107** | **107/107 aprobadas (100%)** |

El reporte detallado con capturas por prueba se regenera automáticamente:

```bash
python -m pytest            # ejecuta la suíte (107 pruebas)
python generar_reportes.py  # genera reporte_tests.html (HTML para presentar)
```

> Para incluir en el capítulo de la tesis: abrir `docs/diagrama_arquitectura.drawio`,
> exportar cada página a imagen (PNG/SVG), y adjuntar `reporte_tests.html` como
> evidencia de las pruebas aplicadas.

---

## Notas de seguridad

- Las contraseñas se almacenan únicamente como hash (Werkzeug).
- Todos los formularios están protegidos contra CSRF.
- Las rutas sensibles verifican autenticación y rol.
- Las variables sensibles se gestionan mediante variables de entorno (`.env`).
- Las consultas se realizan a través del ORM (SQLAlchemy) para evitar
  inyección SQL.
- La eliminación de registros es lógica (no se destruyen datos).
- Cabeceras HTTP de protección: `X-Content-Type-Options`, `X-Frame-Options`,
  `Referrer-Policy`, `Permissions-Policy` y HSTS (en producción).
- Bloqueo temporal tras 5 intentos fallidos de acceso.
- Copias de seguridad accesibles por CLI (`flask backup`).
