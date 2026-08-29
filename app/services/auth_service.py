"""Servicio de autenticación y administración de usuarios."""
from flask_login import current_user, login_user, logout_user

from app.extensions import db
from app.models import RolUsuario, Usuario


def autenticar(usuario: str, password: str) -> Usuario | None:
    """Valida credenciales y devuelve el usuario autenticado.

    Devuelve None si las credenciales son incorrectas, la cuenta no existe
    o está desactivada.
    """
    user = Usuario.query.filter_by(usuario=usuario).first()
    if user is None or not user.activo:
        return None
    if not user.check_password(password):
        return None
    return user


def iniciar_sesion(user: Usuario) -> None:
    """Inicia la sesión y actualiza la fecha de último acceso."""
    user.marcar_sesion()
    db.session.commit()
    login_user(user)


def cerrar_sesion() -> None:
    """Cierra la sesión del usuario actual."""
    logout_user()


def usuario_sesion() -> Usuario | None:
    """Devuelve el usuario de la sesión actual o None."""
    return current_user if current_user.is_authenticated else None


def esta_autenticado() -> bool:
    return current_user.is_authenticated


def crear_usuario(
    nombre: str,
    usuario: str,
    password: str,
    rol: str = RolUsuario.ENCARGADO,
    activo: bool = True,
) -> Usuario:
    """Crea un nuevo usuario con contraseña hasheada."""
    nuevo = Usuario(
        nombre=nombre.strip(),
        usuario=usuario.strip().lower(),
        rol=rol,
        activo=activo,
    )
    nuevo.set_password(password)
    db.session.add(nuevo)
    db.session.commit()
    return nuevo


def existe_usuario(usuario: str) -> bool:
    """Indica si ya existe un usuario con ese nombre de usuario."""
    return db.session.query(
        Usuario.query.filter_by(usuario=usuario.strip().lower()).exists()
    ).scalar()


def listar_usuarios() -> list[Usuario]:
    """Devuelve todos los usuarios ordenados por fecha de creación."""
    return Usuario.query.order_by(Usuario.fecha_creacion.desc()).all()


def cambiar_estado(user: Usuario, activo: bool) -> None:
    """Activa o desactiva una cuenta de usuario."""
    user.activo = activo
    db.session.commit()
