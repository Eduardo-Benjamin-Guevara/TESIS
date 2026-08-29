"""Rutas de monitoreo y reportes: dashboard de indicadores, stock en tiempo real y reportes."""
from datetime import date

from flask import Blueprint, render_template, request
from flask_login import login_required

from app.services import categoria_service, reportes_service

bp = Blueprint("monitoreo", __name__, url_prefix="/monitoreo")


@bp.route("/")
@login_required
def dashboard():
    kpis = reportes_service.kpis()
    actividad = reportes_service.actividad_reciente(limit=8)
    por_categoria = reportes_service.reporte_por_categoria()
    return render_template(
        "monitoreo/dashboard.html",
        kpis=kpis,
        actividad=actividad,
        por_categoria=por_categoria,
    )


@bp.route("/stock")
@login_required
def stock():
    filtro = request.args.get("q", "").strip()
    categoria_id = request.args.get("categoria", "").strip()
    filas = reportes_service.stock_tiempo_real(filtro=filtro, categoria_id=categoria_id)
    return render_template(
        "monitoreo/stock.html",
        filas=filas,
        filtro=filtro,
        categoria_id=categoria_id,
        categorias=categoria_service.listar(),
    )


@bp.route("/reportes")
@login_required
def reportes():
    vencimientos = reportes_service.reporte_vencimientos()
    por_categoria = reportes_service.reporte_por_categoria()
    return render_template(
        "monitoreo/reportes.html",
        vencimientos=vencimientos,
        por_categoria=por_categoria,
        hoy=date.today(),
    )