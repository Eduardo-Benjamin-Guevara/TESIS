"""Servicio de alertas: próximos a vencer y stock bajo, con priorización.

Las alertas se calculan de forma derivada (consultando lotes y stock actual),
sin duplicar estado, lo que evita inconsistencias entre alertas e inventario.

Niveles de prioridad:
- `crítica`: vence en <= 3 días (o ya vencido) / stock en 0.
- `alta`: vence en <= 7 días / stock < 50% del mínimo.
- `media`: vence en <= 15 días / stock <= mínimo.
"""
from datetime import date, timedelta

from app.models import Lote
from app.services import alimento_service


# Umbrales (en días) para las alertas de vencimiento
def umbrales_vencimiento() -> dict:
    """Días límite para cada nivel de alerta de vencimiento."""
    return {"critica": 3, "alta": 7, "media": 15}


def _nivel_vencimiento(dias: int) -> str:
    u = umbrales_vencimiento()
    # días negativos => ya vencido (crítico)
    if dias <= 0:
        return "critica"
    if dias <= u["critica"]:
        return "critica"
    if dias <= u["alta"]:
        return "alta"
    if dias <= u["media"]:
        return "media"
    return ""


def _nivel_stock(alimento) -> str:
    actual = float(alimento.stock_actual or 0)
    minimo = float(alimento.stock_minimo or 0)
    if minimo <= 0:
        return ""  # sin mínimo definido: no aplica alerta
    if actual <= 0:
        return "critica"
    if actual < minimo * 0.5:
        return "alta"
    if actual <= minimo:
        return "media"
    return ""


def proximos_a_vencer():
    """Devuelve las alertas de vencimiento (lotes activos por vencer o vencidos)."""
    u = umbrales_vencimiento()
    hoy = date.today()
    limite = hoy + timedelta(days=u["media"])
    alertas = []
    for lote in Lote.query.filter(Lote.activo.is_(True)).all():
        dias = (lote.fecha_vencimiento - hoy).days
        if dias > u["media"]:
            continue
        nivel = _nivel_vencimiento(dias)
        if not nivel:
            continue
        alertas.append(
            {
                "tipo": "vencimiento",
                "nivel": nivel,
                "lote": lote,
                "alimento": lote.alimento,
                "dias": dias,
                "fecha_vencimiento": lote.fecha_vencimiento,
                "cantidad": float(lote.cantidad or 0),
            }
        )
    return sorted(alertas, key=lambda a: a["dias"])


def stock_bajo():
    """Devuelve las alertas de stock bajo (stock <= mínimo)."""
    alertas = []
    for a in alimento_service.listar(incluir_inactivos=False):
        nivel = _nivel_stock(a)
        if nivel:
            alertas.append(
                {
                    "tipo": "stock",
                    "nivel": nivel,
                    "alimento": a,
                    "stock": float(a.stock_actual or 0),
                    "minimo": float(a.stock_minimo or 0),
                }
            )
    return sorted(
        alertas,
        # críticas primero, y dentro de críticas las con menos stock primero
        key=lambda a: (0 if a["nivel"] == "critica" else (1 if a["nivel"] == "alta" else 2), a["stock"]),
    )


def todas() -> list:
    """Devuelve todas las alertas fusionadas y ordenadas por prioridad."""
    combinadas = proximos_a_vencer() + stock_bajo()
    orden = {"critica": 0, "alta": 1, "media": 2}
    return sorted(combinadas, key=lambda a: orden[a["nivel"]])


def contar() -> dict:
    """Resumen de alertas: total y por prioridad."""
    items = todas()
    resumen = {"total": len(items), "critica": 0, "alta": 0, "media": 0}
    for a in items:
        resumen[a["nivel"]] += 1
    return resumen


def contar_vencidos() -> int:
    """Número de lotes activos ya vencidos."""
    return sum(1 for a in proximos_a_vencer() if a["dias"] < 0)
