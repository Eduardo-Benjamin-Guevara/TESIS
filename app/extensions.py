"""Registro de extensiones de Flask (patrón de extensión única).

Centraliza la creación de extensiones para evitar importaciones circulares.
De aquí se importan en el resto de la aplicación.
"""
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()
