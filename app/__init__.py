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
                mensaje="No tienes permisos para acceder a este recurso.",
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
                mensaje="El recurso que buscas no existe o fue movido.",
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
                titulo="Error interno",
                mensaje="Ocurrió un error inesperado. Inténtalo de nuevo más tarde.",
            ),
            500,
        )


def configurar_logging(app: Flask) -> None:
    """Configura el nivel de log a partir de la configuración."""
    logging.basicConfig(
        level=getattr(logging, app.config.get("LOG_LEVEL", "INFO").upper(), logging.INFO)
    )


def create_app(config_name: str | None = None) -> Flask:
    """Crea y devuelve una instancia configurada de la aplicación."""
    if config_name is None:
        config_name = os.environ.get("FLASK_CONFIG", "development")

    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_by_name.get(config_name, config_by_name["development"]))

    # Asegurar que el directorio de instancia exista (contiene la BD en desarrollo)
    os.makedirs(app.instance_path, exist_ok=True)

    # Inicializar extensiones
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # Configurar seguridad y logging
    configurar_logging(app)

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
