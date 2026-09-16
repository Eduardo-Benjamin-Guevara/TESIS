"""Rutas de autenticación: login y logout."""
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField
from wtforms.validators import DataRequired

from app.services import auth_service

bp = Blueprint("auth", __name__)

MAX_INTENTOS = 5
BLOQUEO_MINUTOS = 5


class LoginForm(FlaskForm):
    usuario = StringField("Usuario", validators=[DataRequired()])
    password = PasswordField("Contraseña", validators=[DataRequired()])


@bp.route("/login", methods=["GET", "POST"])
def login():
    # Si ya está autenticado, ir directo al panel
    if current_user.is_authenticated:
        return redirect(url_for("main.panel"))

    form = LoginForm()

    # Bloqueo temporal tras demasiados intentos fallidos
    bloqueo_hasta = session.get("login_bloqueo_hasta", 0)
    if bloqueo_hasta and __import__("time").time() < bloqueo_hasta:
        restante = int(bloqueo_hasta - __import__("time").time())
        flash(
            f"Demasiados intentos fallidos. Intenta de nuevo en {restante} segundos.",
            "warning",
        )
        return render_template("auth/login.html", form=form)

    if form.validate_on_submit():
        user = auth_service.autenticar(form.usuario.data, form.password.data)
        if user is None:
            intentos = session.get("login_intentos", 0) + 1
            session["login_intentos"] = intentos
            if intentos >= MAX_INTENTOS:
                session["login_bloqueo_hasta"] = __import__("time").time() + BLOQUEO_MINUTOS * 60
                session["login_intentos"] = 0
                flash(
                    f"Demasiados intentos fallidos. Intenta de nuevo en {BLOQUEO_MINUTOS} minutos.",
                    "warning",
                )
            else:
                flash("Credenciales incorrectas o cuenta inactiva.", "danger")
        else:
            # Limpiar contador tras un acceso correcto
            session.pop("login_intentos", None)
            session.pop("login_bloqueo_hasta", None)
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
