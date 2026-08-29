"""Modelo de Usuario y roles.

El diseño queda preparado: la entidad cuenta con campos de auditoría
(fecha_creacion, ultima_sesion) y un rol que permitirá controlar
permisos por tipo de usuario en versiones futuras.
"""
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.utils.timezone import utcnow


class RolUsuario:
    """Roles disponibles en el sistema."""

    ADMIN = "admin"
    ENCARGADO = "encargado"
    CONSULTA = "consulta"

    VALORES = [ADMIN, ENCARGADO, CONSULTA]


class Usuario(db.Model, UserMixin):
    """Representa a un usuario del sistema."""

    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    usuario = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(20), nullable=False, default=RolUsuario.ENCARGADO)
    activo = db.Column(db.Boolean, nullable=False, default=True)
    fecha_creacion = db.Column(db.DateTime, nullable=False, default=utcnow)
    ultima_sesion = db.Column(db.DateTime, nullable=True)

    movimientos = db.relationship("Movimiento", back_populates="usuario", lazy="dynamic")

    # -- Contraseña -----------------------------------------------------
    def set_password(self, password: str) -> None:
        """Genera y almacena el hash seguro de la contraseña."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verifica la contraseña contra el hash almacenado."""
        return check_password_hash(self.password_hash, password)

    # -- Flask-Login ----------------------------------------------------
    def get_id(self):
        return str(self.id)

    @property
    def is_active(self):
        # Respeta el campo `activo` para desactivar cuentas
        return self.activo

    # -- Helpers --------------------------------------------------------
    @property
    def es_admin(self) -> bool:
        return self.rol == RolUsuario.ADMIN

    def marcar_sesion(self) -> None:
        """Actualiza la fecha de la última sesión."""
        self.ultima_sesion = utcnow()

    def __repr__(self):
        return f"<Usuario {self.usuario}>"
