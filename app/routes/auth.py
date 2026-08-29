"""Rutas de autenticación: login y logout."""
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField
from wtforms.validators import DataRequired

from app.services import auth_service

bp = Blueprint("auth", __name__)


class LoginForm(FlaskForm):
    usuario = StringField("Usuario", validators=[DataRequired()])
    password = PasswordField("Contraseña", validators=[DataRequired()])


@bp.route("/login", methods=["GET", "POST"])
def login():
    # Si ya está autenticado, ir directo al panel
    if current_user.is_authenticated:
        return redirect(url_for("main.panel"))

    form = LoginForm()
    if form.validate_on_submit():
        user = auth_service.autenticar(form.usuario.data, form.password.data)
        if user is None:
            flash("Credenciales incorrectas o cuenta inactiva.", "danger")
        else:
            auth_service.iniciar_sesion(user)
            flash(f"¡Bienvenido, {user.nombre}!", "success")
            siguiente = request.args.get("next")
            destino = (
                siguiente
                if siguiente and siguiente.startswith("/")
                else url_for("main.panel")
            )
            return redirect(destino)

    return render_template("auth/login.html", form=form)


@bp.route("/logout")
@login_required
def logout():
    auth_service.cerrar_sesion()
    flash("Has cerrado sesión correctamente.", "info")
    return redirect(url_for("auth.login"))
