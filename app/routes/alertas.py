"""Rutas del sistema de alertas: próximos a vencer y stock bajo."""
from flask import Blueprint, render_template
from flask_login import login_required

from app.services import alertas_service

bp = Blueprint("alertas", __name__, url_prefix="/alertas")

# Etiquetas y colores por nivel de prioridad
BADGES = {
    "critica": ("Critica", "bg-danger"),
    "alta": ("Alta", "bg-warning text-dark"),
    "media": ("Media", "bg-info text-dark"),
}


@bp.route("/")
@login_required
def index():
    alertas = alertas_service.todas()
    vencimiento = alertas_service.proximos_a_vencer()
    stock = alertas_service.stock_bajo()
    resumen = alertas_service.contar()
    return render_template(
        "alertas/index.html",
        alertas=alertas,
        vencimiento=vencimiento,
        stock=stock,
        resumen=resumen,
        badges=BADGES,
    )


@bp.route("/vence-pronto")
@login_required
def vence_pronto():
    vencimiento = alertas_service.proximos_a_vencer()
    resumen = alertas_service.contar()
    return render_template(
        "alertas/vencimiento.html",
        vencimiento=vencimiento,
        resumen=resumen,
        badges=BADGES,
    )


@bp.route("/stock-bajo")
@login_required
def stock_bajo():
    stock = alertas_service.stock_bajo()
    resumen = alertas_service.contar()
    return render_template(
        "alertas/stock_bajo.html",
        stock=stock,
        resumen=resumen,
        badges=BADGES,
    )
