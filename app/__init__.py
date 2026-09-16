"""Fábrica de aplicación Flask (application factory).

Centraliza la creación y configuración de la aplicación, la inicialización
de extensiones, los blueprints y las tareas de arranque.
"""
import logging
import os

from dotenv import load_dotenv
from flask import Flask, render_template
from flask_login import LoginManager

from app.config import config_by_name
from app.extensions import csrf, db, migrate

# Cargar variables de entorno desde `.env` si existe
load_dotenv()


def registrar_errores(app: Flask) -> None:
    """Registra los manejadores de errores HTTP más comunes."""

    @app.errorhandler(403)
    def prohibido(_):
        return (
            render_template(
                "errors/403.html",
                codigo=403,
                icono="bi-shield-lock",
                titulo="Acceso denegado",
                mensaje="No tienes permisos para ver esta sección. "
                "Contacta al administrador si crees que es un error.",
            ),
            403,
        )

    @app.errorhandler(404)
    def no_encontrado(_):
        return (
            render_template(
                "errors/404.html",
                codigo=404,
                icono="bi-search",
                titulo="Página no encontrada",
                mensaje="La dirección que escribiste no existe o fue movida.",
            ),
            404,
        )

    @app.errorhandler(500)
    def error_interno(_):
        db.session.rollback()
        return (
            render_template(
                "errors/500.html",
                codigo=500,
                icono="bi-bug",
                titulo="Algo salió mal",
                mensaje="Ocurrió un error inesperado. Prueba de nuevo en unos minutos.",
            ),
            500,
        )


def configurar_logging(app: Flask) -> None:
    """Configura el nivel de log a partir de la configuración."""
    logging.basicConfig(
        level=getattr(logging, app.config.get("LOG_LEVEL", "INFO").upper(), logging.INFO)
    )


def agregar_cabeceras_seguridad(app: Flask) -> None:
    """Añade cabeceras de seguridad básicas a todas las respuestas."""

    @app.after_request
    def _cabeceras_seguridad(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        # HSTS solo en producción (HTTPS)
        if not app.config.get("DEBUG", False) and not app.config.get("TESTING", False):
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return response


def inicializar_bd(app: Flask) -> None:
    """Crea las tablas (si no existen) y siembra datos básicos.

    Es idempotente y segura: si la base de datos ya tiene datos, no los
    duplica. Se llama al crear la app para que, en cualquier entorno
    (Local, Render, Vercel, etc.), las tablas y los datos iniciales existan.

    En plataformas serverless (Vercel) varios procesos pueden arrancar a la
    vez y ejecutar esta rutina en paralelo contra la misma base de datos.
    Para evitarlo, el sembrado se reintenta si ocurre una colisión de claves
    únicas (otro proceso ya creó esos registros); basta con hacer rollback y
    comprobar de nuevo.
    """
    from sqlalchemy import inspect as sa_inspect
    from sqlalchemy.exc import IntegrityError

    from app.services.simulacion_service import (
        existen_datos_demo,
        generar_datos_demo,
    )

    def _sembrar() -> None:
        """Ejecuta la secuencia completa de siembra."""
        from app.models.usuario import Usuario
        from app.services.init_services import (
            crear_admin_inicial,
            sembrar_categorias,
        )

        sembrar_categorias()
        if not Usuario.query.filter_by(rol="admin").first():
            crear_admin_inicial()
        if not existen_datos_demo():
            generar_datos_demo()

    with app.app_context():
        if "categorias" in sa_inspect(db.engine).get_table_names():
            # La BD ya tiene tablas: solo aseguramos datos mínimos
            for intento in range(4):
                try:
                    _sembrar()
                    break
                except IntegrityError:
                    if intento == 3:
                        raise
                    db.session.rollback()
        else:
            # BD vacía: creamos todo desde cero
            db.create_all()
            for intento in range(4):
                try:
                    _sembrar()
                    break
                except IntegrityError:
                    if intento == 3:
                        raise
                    db.session.rollback()


def create_app(config_name: str | None = None) -> Flask:
    """Crea y devuelve una instancia configurada de la aplicación."""
    if config_name is None:
        config_name = os.environ.get("FLASK_CONFIG", "development")

    # En Vercel los estáticos se sirven desde public/ (CDN). En local Flask los
    # sirve desde la misma carpeta para mantener la misma URL /static/...
    _RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app = Flask(
        __name__,
        instance_relative_config=True,
        static_folder=os.path.join(_RAIZ, "public", "static"),
    )
    app.config.from_object(config_by_name.get(config_name, config_by_name["development"]))

    # Asegurar que el directorio de instancia exista (contiene la BD en desarrollo).
    # En entornos serverless (Vercel) el filesystem de código es de solo
    # lectura: si falla, simplemente continuamos (la BD se gestiona por DATABASE_URL).
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass

    # Inicializar extensiones
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # Configurar seguridad y logging
    configurar_logging(app)
    agregar_cabeceras_seguridad(app)

    # Flask-Login
    login_manager = LoginManager(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Debes iniciar sesión para acceder."
    login_manager.login_message_category = "warning"

    from app.models import Usuario

    @login_manager.user_loader
    def cargar_usuario(user_id):
        return db.session.get(Usuario, int(user_id))

    # Registrar blueprints
    from app.routes import (
        alimentos_bp,
        alertas_bp,
        auth_bp,
        categorias_bp,
        inventario_bp,
        lotes_bp,
        main_bp,
        monitoreo_bp,
        notificaciones_bp,
        usuarios_bp,
    )

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(alimentos_bp)
    app.register_blueprint(categorias_bp)
    app.register_blueprint(inventario_bp)
    app.register_blueprint(lotes_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(alertas_bp)
    app.register_blueprint(monitoreo_bp)
    app.register_blueprint(notificaciones_bp)

    # Registrar errores
    registrar_errores(app)

    # Comandos CLI (flask ...)
    from app.cli import registrar_cli

    registrar_cli(app)

    # Inicializar base de datos (tablas + datos mínimos) fuera del entorno de prueba
    if not app.config.get("TESTING", False):
        inicializar_bd(app)

    # Contexto global para plantillas: categorías y resumen de alertas
    @app.context_processor
    def inyectar_contexto():
        from flask_login import current_user

        from app.services import alertas_service, categoria_service, notificaciones_service

        contexto = {"categorias": categoria_service.listar()}
        # Contador de alertas para el badge del sidebar (solo con sesión)
        if current_user.is_authenticated:
            contexto["alerta_total"] = alertas_service.contar()["total"]
            # Notificaciones no leídas para la campana del topbar
            contexto["notif_no_leidas"] = notificaciones_service.notificaciones_usuario(
                current_user
            )["no_leidas"]
        else:
            contexto["alerta_total"] = 0
            contexto["notif_no_leidas"] = 0
        return contexto

    return app
