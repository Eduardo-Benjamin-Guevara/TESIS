"""Servicio de monitoreo y reportes: KPIs, stock en tiempo real e indicadores."""
from datetime import date, timedelta

from app.models import Categoria, Lote, Movimiento, TipoMovimiento
from app.services import alimento_service, alertas_service


def _dias_media():
    return alertas_service.umbrales_vencimiento()["media"]


def kpis() -> dict:
    """Indicadores clave (KPIs) del inventario."""
    alimentos = alimento_service.listar()
    activos = [a for a in alimentos if a.activo]
    alertas = alertas_service.contar()
    vencimiento = alertas_service.proximos_a_vencer()

    stock_total = sum(float(a.stock_actual or 0) for a in activos)
    con_stock = sum(1 for a in activos if float(a.stock_actual or 0) > 0)
    stock_bajo = [a for a in activos if a.stock_bajo]

    movs = Movimiento.query.all()
    entradas = sum(1 for m in movs if m.tipo == TipoMovimiento.ENTRADA)
    salidas = sum(1 for m in movs if m.tipo == TipoMovimiento.SALIDA)

    return {
        "total_alimentos": len(activos),
        "total_categorias": Categoria.query.count(),
        "stock_total": stock_total,
        "con_stock": con_stock,
        "stock_bajo": len(stock_bajo),
        "alertas_activas": alertas["total"],
        "alertas_criticas": alertas["critica"],
        "proximos_vencer": len(vencimiento),
        "vencidos": alertas_service.contar_vencidos(),
        "total_movimientos": len(movs),
        "entradas": entradas,
        "salidas": salidas,
    }


def stock_tiempo_real(filtro: str = "", categoria_id: str = ""):
    """Stock en tiempo real (estado derivado del inventario) con filtros."""
    alimentos = alimento_service.listar(filtro=filtro, categoria_id=categoria_id)
    filas = []
    for a in alimentos:
        total, lotes = 0.0, []
        for l in a.lotes:
            if l.activo and float(l.cantidad or 0) > 0:
                lotes.append(l)
                total += float(l.cantidad or 0)
        # El stock real de referencia es el campo stock_actual (se mantiene
        # con los movimientos). El desglose por lote es informativo.
        filas.append(
            {
                "alimento": a,
                "stock": float(a.stock_actual or 0),
                "lotes": lotes,
            }
        )
    return filas


def reporte_vencimientos(proximos_dias: int | None = None) -> list:
    """Reporte de lotes por vencer/vencidos, agrupado por alimento."""
    if proximos_dias is None:
        proximos_dias = _dias_media()
    hoy = date.today()
    limite = hoy + timedelta(days=proximos_dias)
    lotes = [
        l for l in Lote.query.filter(Lote.activo.is_(True)).all()
        if l.fecha_vencimiento <= limite
    ]
    lotes.sort(key=lambda l: l.fecha_vencimiento)
    return lotes


def reporte_por_categoria() -> list:
    """Cantidad de alimentos y stock por categoría."""
    categorias = Categoria.query.all()
    filas = []
    for c in categorias:
        alimentos = c.alimentos if hasattr(c, "alimentos") else []
        activos = [a for a in alimentos if a.activo]
        filas.append(
            {
                "categoria": c,
                "cantidad": len(activos),
                "stock": sum(float(a.stock_actual or 0) for a in activos),
                "bajo": sum(1 for a in activos if a.stock_bajo),
            }
        )
    return filas


def actividad_reciente(limit: int = 10) -> list:
    """Últimos movimientos registrados (actividad del inventario)."""
    return (
        Movimiento.query.order_by(Movimiento.fecha.desc()).limit(limit).all()
    )
