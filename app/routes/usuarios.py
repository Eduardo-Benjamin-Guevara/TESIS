"""Rutas de administración de usuarios (solo admin)."""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, SelectField, StringField
from wtforms.validators import DataRequired, Length, Optional

from app.models import RolUsuario
from app.services import auth_service
from app.utils.decorators import rol_requerido

bp = Blueprint("usuarios", __name__, url_prefix="/usuarios")


class UsuarioForm(FlaskForm):
    nombre = StringField(
        "Nombre completo", validators=[DataRequired()], render_kw={"maxlength": "120"}
    )
    usuario = StringField(
        "Usuario", validators=[DataRequired(), Length(min=3, max=80)],
        render_kw={"maxlength": "80"},
    )
    password = PasswordField(
        "Contraseña",
        validators=[Optional(), Length(min=6)],
        render_kw={"maxlength": "255"},
    )
    rol = SelectField(
        "Rol",
        choices=[(r, r.capitalize()) for r in RolUsuario.VALORES],
        default=RolUsuario.ENCARGADO,
    )
    activo = BooleanField("Activo", default=True)


@bp.route("/")
@rol_requerido("admin")
def index():
    usuarios = auth_service.listar_usuarios()
    return render_template("usuarios/index.html", usuarios=usuarios)


@bp.route("/nuevo", methods=["GET", "POST"])
@rol_requerido("admin")
def nuevo():
    form = UsuarioForm()
    if form.validate_on_submit():
        usuario_nombre = form.usuario.data.strip().lower()
        if auth_service.existe_usuario(usuario_nombre):
            flash("Ya existe un usuario con ese nombre de usuario.", "danger")
        elif not form.password.data:
            flash("La contraseña es obligatoria al crear un usuario.", "danger")
        else:
            auth_service.crear_usuario(
                nombre=form.nombre.data,
                usuario=usuario_nombre,
                password=form.password.data,
                rol=form.rol.data,
                activo=form.activo.data,
            )
            flash("Usuario creado correctamente.", "success")
            return redirect(url_for("usuarios.index"))
    return render_template("usuarios/form.html", form=form, titulo="Nuevo usuario")


@bp.route("/<int:usuario_id>/estado", methods=["POST"])
@rol_requerido("admin")
def cambiar_estado(usuario_id):
    from app.models import Usuario
    from app.extensions import db
    from flask_login import current_user

    user = db.session.get(Usuario, usuario_id)
    if user is None:
        abort(404)
    if user.id == current_user.id:
        flash("No puedes desactivar tu propia cuenta.", "danger")
        return redirect(url_for("usuarios.index"))

    auth_service.cambiar_estado(user, not user.activo)
    estado = "activado" if user.activo else "desactivado"
    flash(f"Usuario {estado}.", "success")
    return redirect(url_for("usuarios.index"))
