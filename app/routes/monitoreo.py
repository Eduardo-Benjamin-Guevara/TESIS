"""Rutas de monitoreo y reportes: dashboard de indicadores, stock en tiempo real y reportes."""
from datetime import date

from flask import Blueprint, Response, render_template, request
from flask_login import login_required

from app.services import (
    categoria_service,
    exportacion_service,
    recomendaciones_service,
    reportes_service,
)

bp = Blueprint("monitoreo", __name__, url_prefix="/monitoreo")


def _datos_graficos():
    """Datos preparados para los gráficos Chart.js del dashboard."""
    por_categoria = reportes_service.reporte_por_categoria()
    categorias = [f["categoria"].nombre.capitalize() for f in por_categoria]
    stock_cat = [round(f["stock"], 2) for f in por_categoria]

    kpis = reportes_service.kpis()
    estado = {
        "labels": ["Stock óptimo", "Stock bajo", "Vencidos"],
        "datos": [
            max(kpis["total_alimentos"] - kpis["stock_bajo"], 0),
            kpis["stock_bajo"],
            kpis["vencidos"],
        ],
    }
    movimientos = {
        "labels": ["Entradas", "Salidas"],
        "datos": [kpis["entradas"], kpis["salidas"]],
    }
    return {
        "stock_por_categoria": {"labels": categorias, "datos": stock_cat},
        "estado_inventario": estado,
        "movimientos": movimientos,
    }


@bp.route("/")
@login_required
def dashboard():
    kpis = reportes_service.kpis()
    actividad = reportes_service.actividad_reciente(limit=8)
    por_categoria = reportes_service.reporte_por_categoria()
    graficos = _datos_graficos()
    return render_template(
        "monitoreo/dashboard.html",
        kpis=kpis,
        actividad=actividad,
        por_categoria=por_categoria,
        graficos=graficos,
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


@bp.route("/recomendaciones")
@login_required
def recomendaciones():
    items = recomendaciones_service.recomendaciones()
    return render_template("monitoreo/recomendaciones.html", items=items)


@bp.route("/reportes/exportar")
@login_required
def exportar():
    """Exporta los reportes en formato CSV o Excel."""
    formato = request.args.get("formato", "csv").lower()
    hoy = date.today()

    reportes = []
    vencimientos = reportes_service.reporte_vencimientos()
    for l in vencimientos:
        reportes.append(
            {
                "codigo": l.alimento.codigo,
                "alimento": l.alimento.nombre,
                "lote": l.codigo or f"Lote {l.id}",
                "fecha_vencimiento": l.fecha_vencimiento.isoformat(),
                "cantidad": float(l.cantidad),
                "unidad": l.alimento.unidad_medida,
                "dias_restantes": (l.fecha_vencimiento - hoy).days,
            }
        )
    por_categoria = reportes_service.reporte_por_categoria()
    for f in por_categoria:
        reportes.append(
            {
                "codigo": f"CAT:{f['categoria'].nombre}",
                "alimento": f"Alimentos de {f['categoria'].nombre}",
                "lote": "",
                "fecha_vencimiento": "",
                "cantidad": float(f["stock"]),
                "unidad": "u",
                "dias_restantes": "",
            }
        )

    nombre_archivo = "reporte_inventario"
    if formato == "xlsx":
        contenido = exportacion_service.exportar_excel("Inventario", reportes)
        return Response(
            contenido,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="{nombre_archivo}.xlsx"'
            },
        )

    contenido = exportacion_service.exportar_csv(reportes)
    return Response(
        contenido,
        mimetype="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{nombre_archivo}.csv"'},
    )