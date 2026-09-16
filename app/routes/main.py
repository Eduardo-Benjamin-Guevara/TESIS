"""Rutas principales del panel."""
from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.services import (
    alertas_service,
    alimento_service,
    auth_service,
    simulacion_service,
)

bp = Blueprint("main", __name__)


@bp.route("/robots.txt")
def robots():
    """Permite a los buscadores indexar el sitio (SEO básico)."""
    texto = (
        "User-agent: *\n"
        "Allow: /\n"
        "Disallow: /login\n"
        "Disallow: /demo/\n"
        f"Sitemap: {request.url_root}sitemap.xml\n"
    )
    return texto, 200, {"Content-Type": "text/plain"}


@bp.route("/sitemap.xml")
def sitemap():
    """Sitemap XML con las rutas públicas del sistema (SEO básico)."""
    rutas = ["/", "/login"]
    base = request.url_root.rstrip("/")
    urls = "\n".join(
        f"  <url><loc>{base}{ruta}</loc></url>" for ruta in rutas
    )
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{urls}
</urlset>
"""
    return xml, 200, {"Content-Type": "application/xml"}


@bp.route("/health")
def health():
    """Comprobación de salud para pingers (mantiene vivo el servicio)."""
    return jsonify({"estado": "ok", "servicio": "sistema-alimentos"})


@bp.route("/")
@login_required
def panel():
    total_alimentos = alimento_service.contar_total()
    stock_bajo = [
        a for a in alimento_service.listar() if a.stock_bajo
    ]
    alertas = alertas_service.contar()
    vencimiento = alertas_service.proximos_a_vencer()
    return render_template(
        "main/panel.html",
        total_alimentos=total_alimentos,
        stock_bajo=stock_bajo,
        alertas=alertas,
        vencimiento=vencimiento,
        usuario=auth_service.usuario_sesion(),
        tiene_datos_demo=simulacion_service.existen_datos_demo(),
    )


@bp.post("/demo/datos")
@login_required
def cargar_datos_demo():
    """Carga (o regenera) los datos de simulación. Solo administradores."""
    if not current_user.es_admin:
        flash("No tienes permisos para cargar datos de demostración.", "error")
        return redirect(url_for("main.panel"))
    forzar = request.form.get("accion") == "regenerar"
    resumen = simulacion_service.generar_datos_demo(forzar=forzar)
    flash(
        f"Datos de demostración listos: {resumen['alimentos']} alimentos, "
        f"{resumen['lotes']} lotes y {resumen['movimientos']} movimientos.",
        "success",
    )
    return redirect(url_for("main.panel"))
