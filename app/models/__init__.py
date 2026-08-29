"""Modelos SQLAlchemy para la base de datos.

Cada entidad se define en un módulo dentro de `app/models`.
"""
from app.models.alimento import Alimento
from app.models.usuario import RolUsuario, Usuario

__all__ = ["Alimento", "Usuario", "RolUsuario"]
