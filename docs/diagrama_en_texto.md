# Arquitectura del Sistema — Descripción para dibujar el diagrama

Esta guía describe el diagrama de arquitectura **caja por caja** para
reproducirlo en cualquier herramienta (draw.io, Lucidchart, Word,
PowerPoint). Se indican componentes, flechas y etiquetas.

---

## 1. Idea general (3 bloques)

```
┌────────────────────────────────┐
│  1. USUARIO (Navegador)        │
│  HTML5 · CSS3 · JavaScript     │
│  Bootstrap 5 · Chart.js        │
└───────────────┬────────────────┘
                │ Internet (HTTPS)
┌───────────────▼────────────────┐
│  2. SERVIDOR (Vercel)          │
│  Función Python · Flask        │
│  (presentación + lógica +      │
│   acceso a datos)              │
└───────────────┬────────────────┘
                │ Conexión a BD (DATABASE_URL)
┌───────────────▼────────────────┐
│  3. BASE DE DATOS              │
│  PostgreSQL (Neon)             │
│  tablas: usuario, alimento,    │
│  categoria, lote, movimiento,  │
│  notificacion                  │
└────────────────────────────────┘
```

---

## 2. Detalle del servidor (bloque 2)

```
┌──────────────────────────────────────────────────────────┐
│  SERVIDOR — Vercel (función serverless WSGI)             │
│                                                          │
│  [api/index.py]  →  [create_app() fábrica de Flask]      │
│        │                        │                        │
│        │                        ├──► BLUEPRINTS (rutas): │
│        │                        │    auth · alimentos ·  │
│        │                        │    categorias ·        │
│        │                        │    inventario · lotes  │
│        │                        │    usuarios · alertas  │
│        │                        │    monitoreo ·         │
│        │                        │    notificaciones ·    │
│        │                        │    main                │
│        │                        │         │              │
│        │                        ▼         ▼              │
│        │              [SERVICIOS] (lógica de negocio)    │
│        │              15 servicios: auth, alimento,      │
│        │              inventario, alertas, reportes,     │
│        │              exportacion, recomendaciones,      │
│        │              trazabilidad, qr, backup, etc.     │
│        │                        │                        │
│        │                        ▼                        │
│        │              [MODELOS] (SQLAlchemy)             │
│        │              Usuario · Alimento · Categoria     │
│        │              Lote · Movimiento · Notificacion   │
│        │                        │                        │
│        │              [EXTENSIONES]                      │
│        │              SQLAlchemy · Flask-Migrate ·       │
│        │              Flask-WTF (CSRF) · Flask-Login     │
│        │                        │                        │
│        └────────────────────────┼────► [public/static]   │
│                                 │      CSS · JS · favicon│
│                                 │      (servido por CDN) │
└─────────────────────────────────┼────────────────────────┘
                                  │
                        [PostgreSQL / SQLite]
```

---

## 3. Flechas y etiquetas

| # | De | A | Etiqueta |
|---|---|---|---|
| 1 | Navegador | Vercel | Internet · HTTPS |
| 2 | Navegador | public/static | Archivos estáticos /static/... |
| 3 | api/index.py | create_app() | Bootstrap de la app |
| 4 | create_app() | Blueprints | Registra rutas |
| 5 | Blueprints | Servicios | Delega lógica de negocio |
| 6 | Servicios | Modelos | Acceso a datos (ORM) |
| 7 | Modelos | Base de datos | Conexión (DATABASE_URL) |
| 8 | create_app() | Extensiones | Inicializa extensiones |

---

## 4. Resumen por capa (para el texto del capítulo)

1. **Presentación**: Navegador, plantillas Jinja2, Bootstrap 5, Chart.js.
   Los archivos estáticos (CSS/JS/iconos) se sirven por CDN.
2. **Aplicación**: Python/Flask en Vercel; patrón *application factory*
   (`create_app()`), blueprints (rutas), servicios (lógica) y modelos (ORM).
3. **Datos**: PostgreSQL en Neon (producción) y SQLite (desarrollo),
   con SQLAlchemy y migraciones Alembic (`Flask-Migrate`).
4. **Seguridad**: Flask-Login (sesiones), Flask-WTF (CSRF), hash de
   contraseñas (Werkzeug) y cookies seguras.

---

## 5. Sugerencia de colores (opcional)

- Navegador / cliente: naranja claro.
- Contenedor servidor (Vercel): gris punteado.
- Rutas (blueprints) y fábrica: azul claro.
- Servicios: verde claro.
- Modelos: morado claro.
- Extensiones: amarillo claro.
- Estáticos: rojo claro.
- Base de datos: azul medio con texto blanco.