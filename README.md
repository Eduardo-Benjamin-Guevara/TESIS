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
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   └── img/
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
  hash seguro (Werkzeug).
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
- **Interfaz profesional responsive** con sidebar, barra superior,
  formularios, tablas, mensajes flash y páginas de error (403/404/500).
- **Seguridad**: hash de contraseñas, CSRF, variables sensibles en `.env`,
  uso del ORM (sin SQL inyección), mensajes de error controlados y BCC de
  baja lógica.

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

Cada sprint incluye: **pruebas funcionales, verificación de requerimientos,
identificación y corrección de errores, y evaluación del incremento**.

Para consultar el detalle de cada sprint: `docs/sprintN.md`.

Se contempla también la migración a **PostgreSQL** en producción (la
arquitectura ya está preparada para ello).


---

## Notas de seguridad

- Las contraseñas se almacenan únicamente como hash (Werkzeug).
- Todos los formularios están protegidos contra CSRF.
- Las rutas sensibles verifican autenticación y rol.
- Las variables sensibles se gestionan mediante variables de entorno.
- Las consultas se realizan a través del ORM (SQLAlchemy) para evitar
  inyección SQL.
- La eliminación de registros es lógica (no se destruyen datos).
