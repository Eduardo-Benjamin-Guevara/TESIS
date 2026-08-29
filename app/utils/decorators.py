"""Decoradores de acceso personalizados.

Incluye protección de rutas por autenticación (a través de Flask-Login)
y un decorador de rol para restringir funcionalidades administrativas.
"""
from functools import wraps

from flask import abort, flash, redirect, url_for
from flask_login import current_user


def rol_requerido(*roles):
    """Restringe el acceso a un conjunto de roles.

    Si el usuario no está autenticado, redirige al login. Si lo está pero
    no tiene el rol requerido, responde 403.
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("Debes iniciar sesión para acceder.", "warning")
                return redirect(url_for("auth.login", next=request_url()))
            if current_user.rol not in roles:
                abort(403)
            return view_func(*args, **kwargs)

        return wrapped

    return decorator


def request_url():
    from flask import request

    return request.url if request.method == "GET" else None
