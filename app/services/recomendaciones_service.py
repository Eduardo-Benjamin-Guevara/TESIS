"""Servicio de recomendaciones de compra basadas en el stock bajo.

Sugiere reabastecer los alimentos cuyo stock está por debajo del mínimo,
proponiendo una cantidad objetivo (stock_minimo * 2) para disponer de margen.
"""
from app.services import alimento_service


FACTOR_OBJETIVO = 2.0


def recomendaciones() -> list:
    """Devuelve las recomendaciones de compra priorizadas por urgencia."""
    items = []
    for a in alimento_service.listar():
        actual = float(a.stock_actual or 0)
        minimo = float(a.stock_minimo or 0)
        if minimo <= 0:
            continue
        objetivo = minimo * FACTOR_OBJETIVO
        if actual < minimo:
            faltante = minimo - actual
            cantidad_sugerida = objetivo - actual
            if cantidad_sugerida < faltante:
                cantidad_sugerida = faltante
            items.append(
                {
                    "alimento": a,
                    "actual": actual,
                    "minimo": minimo,
                    "objetivo": objetivo,
                    "faltante": faltante,
                    "cantidad_sugerida": cantidad_sugerida,
                    "urgente": actual <= 0,
                }
            )
    # urgentes primero; dentro del mismo grupo, mayor faltante primero
    items.sort(
        key=lambda r: (0 if r["urgente"] else 1, -r["faltante"])
    )
    return items