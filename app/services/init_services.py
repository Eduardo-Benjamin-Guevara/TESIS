"""Tareas de inicialización de la aplicación.

Se ejecutan al arrancar en el entorno de desarrollo para garantizar que
exista un usuario administrador inicial. Las credenciales se toman de las
variables de entorno (ver `.env`) y nunca se fijan en el código fuente.
"""
import logging

from app.extensions import db
from app.models import RolUsuario, Usuario

logger = logging.getLogger(__name__)


def crear_admin_inicial() -> None:
    """Crea el usuario administrador inicial si no existe.

    Solo actúa cuando la variable `CREATE_ADMIN_ON_START` está habilitada
    (configuración de desarrollo). En producción se debe gestionar al
    administrador mediante un comando o procedimiento seguro.
    """
    from flask import current_app

    if not current_app.config.get("CREATE_ADMIN_ON_START", True):
        return

    nombre = current_app.config["ADMIN_NOMBRE"]
    usuario = current_app.config["ADMIN_USUARIO"]
    password = current_app.config["ADMIN_PASSWORD"]
    rol = current_app.config["ADMIN_ROL"]

    # Si la contraseña es la plantilla por defecto, emitimos una advertencia.
    if password == "change-me-admin":
        logger.warning(
            "El usuario administrador usa la contraseña por defecto. "
            "Configura ADMIN_PASSWORD en tu archivo .env."
        )

    if Usuario.query.filter_by(usuario=usuario).first():
        return

    admin = Usuario(
        nombre=nombre,
        usuario=usuario,
        rol=rol if rol in RolUsuario.VALORES else RolUsuario.ADMIN,
        activo=True,
    )
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()
    logger.info("Usuario administrador inicial creado: %s", usuario)
