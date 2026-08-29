"""Rutas principales del panel."""
from flask import Blueprint, render_template
from flask_login import login_required

from app.services import alimento_service, auth_service

bp = Blueprint("main", __name__)


@bp.route("/")
@login_required
def panel():
    total_alimentos = alimento_service.contar_total()
    stock_bajo = [
        a for a in alimento_service.listar() if a.stock_bajo
    ]
    return render_template(
        "main/panel.html",
        total_alimentos=total_alimentos,
        stock_bajo=stock_bajo,
        usuario=auth_service.usuario_sesion(),
    )
