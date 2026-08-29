"""Registro de blueprints de la aplicación."""
from app.routes.alimentos import bp as alimentos_bp
from app.routes.alertas import bp as alertas_bp
from app.routes.auth import bp as auth_bp
from app.routes.categorias import bp as categorias_bp
from app.routes.inventario import bp as inventario_bp
from app.routes.lotes import bp as lotes_bp
from app.routes.main import bp as main_bp
from app.routes.usuarios import bp as usuarios_bp

__all__ = [
    "alimentos_bp",
    "alertas_bp",
    "auth_bp",
    "categorias_bp",
    "inventario_bp",
    "lotes_bp",
    "main_bp",
    "usuarios_bp",
]
