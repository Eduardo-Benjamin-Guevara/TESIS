# Sprint 12 — Migración de hosting a Render.com

## Objetivo

Restablecer el sistema en línea tras la caída del despliegue serverless de
Vercel (`FUNCTION_INVOCATION_FAILED` intermitente en la función WSGI),
migrando a **Render.com**, host que mantiene el servicio web activo de forma
continua en su plan gratuito (sin función serverless).

## Qué se hizo

1. **`render.yaml`** (Infrastructure as Code de Render): define el servicio web
   `control-alimentos` (Python + Gunicorn) y su **base de datos PostgreSQL
   gratuita** autocontenida. Al conectar el repositorio con "New → Blueprint",
   Render crea ambos sin pasos manuales:
   - `buildCommand`: `pip install -r requirements.txt`.
   - `startCommand`: `gunicorn run:app --workers 1 --threads 2 --timeout 90`.
   - `healthCheckPath`: `/login` (página pública sin BD).
   - Variables: `FLASK_CONFIG=production`, `SECRET_KEY` (generada),
     `DATABASE_URL` (desde la BD de Render), `CREATE_ADMIN_ON_START=true`,
     admin inicial, `SESSION_COOKIE_SECURE=true`.
2. **README**: sección "Despliegue gratis (Render.com — recomendado)" con los
   3 pasos (cuenta, Blueprint, URL) y los límites del plan gratis. La sección
   de Vercel queda marcada como alternativa **no recomendada** (se conserva
   configuración para reintentar en el futuro).

## Verificación

La app se probó localmente en configuración producción: `/login` responde 200,
`/` redirige a login y el arranque WSGI es estable.

Pruebas: 107/107 aprobadas (120s).