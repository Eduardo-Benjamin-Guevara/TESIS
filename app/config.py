"""Configuración de la aplicación.

Utiliza variables de entorno (cargadas desde `.env`) para no exponer datos
sensibles en el código. Esta configuración está pensada para ser fácilmente
sustituible en producción (por ejemplo, apuntando a PostgreSQL).
"""
import os
from datetime import timedelta


class BaseConfig:
    """Configuración base común a todos los entornos."""

    # Seguridad
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-insecure-change-me")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    # Cookie de sesión solo por HTTPS en producción
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"
    REMEMBER_COOKIE_DURATION = timedelta(days=30)

    # Base de datos
    # Leemos la URI desde el entorno. Por defecto SQLite de desarrollo.
    # En producción basta con definir SQLALCHEMY_DATABASE_URI en `.env`
    # apuntando a PostgreSQL (p. ej. postgresql://user:pass@host/db).
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "SQLALCHEMY_DATABASE_URI", "sqlite:///" + os.path.join(
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "instance")),
            "sistema_alimentos.db",
        )
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }

    # WTF / CSRF
    WTF_CSRF_TIME_LIMIT = 3600

    # Logs
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

    # Datos del usuario administrador inicial
    ADMIN_NOMBRE = os.environ.get("ADMIN_NOMBRE", "Administrador")
    ADMIN_USUARIO = os.environ.get("ADMIN_USUARIO", "admin")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
    ADMIN_ROL = os.environ.get("ADMIN_ROL", "admin")


class DevelopmentConfig(BaseConfig):
    """Configuración para desarrollo."""
    DEBUG = True


class TestingConfig(BaseConfig):
    """Configuración para pruebas automatizadas."""
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    # Evitar que la creación del admin interfiera en las pruebas
    CREATE_ADMIN_ON_START = False


class ProductionConfig(BaseConfig):
    """Configuración para producción."""
    DEBUG = False
    TESTING = False


# Mapa para seleccionar configuración mediante FLASK_CONFIG
config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
