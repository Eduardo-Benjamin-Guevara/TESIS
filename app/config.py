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
    # Cookie de sesión solo por HTTPS (se activa automáticamente en producción)
    SESSION_COOKIE_SECURE = (
        True
        if os.environ.get("FLASK_CONFIG", "development") == "production"
        else os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"
    )
    REMEMBER_COOKIE_DURATION = timedelta(days=30)

    # Base de datos
    # Por defecto usa SQLite en `instance/` (solo desarrollo). En producción
    # (Render, Vercel, Railway, etc.) se debe apuntar a PostgreSQL mediante
    # DATABASE_URL o SQLALCHEMY_DATABASE_URI.
    _BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    _INSTANCE_DIR = os.path.join(_BASE_DIR, "instance")
    try:
        # En entornos serverless (Vercel) el sistema de archivos es de solo
        # lectura: no intentar crear directorios si falla.
        os.makedirs(_INSTANCE_DIR, exist_ok=True)
    except OSError:
        pass
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        os.environ.get(
            "SQLALCHEMY_DATABASE_URI",
            "sqlite:///" + os.path.join(_INSTANCE_DIR, "sistema_alimentos.db"),
        ),
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }

    # WTF / CSRF
    WTF_CSRF_TIME_LIMIT = 3600

    # Rendimiento: cachear assets estáticos durante 7 días (los cambios
    # se versionan con ?v=N en las plantillas).
    SEND_FILE_MAX_AGE_DEFAULT = timedelta(days=7)

    # Logs
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

    # Datos del usuario administrador inicial
    ADMIN_NOMBRE = os.environ.get("ADMIN_NOMBRE", "Administrador")
    ADMIN_USUARIO = os.environ.get("ADMIN_USUARIO", "admin")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
    ADMIN_ROL = os.environ.get("ADMIN_ROL", "admin")

    # Analytics opcional (Google Analytics/Gtag). Vacío = desactivado.
    ANALYTICS_TAG = os.environ.get("ANALYTICS_TAG", "")


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
