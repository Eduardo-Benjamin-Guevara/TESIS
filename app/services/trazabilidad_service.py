"""Servicio de trazabilidad total de un alimento.

Permite reconstruir el historial completo de un alimento: todos los
movimientos (entradas y salidas) con su fecha, cantidad, stock resultante,
motivo, usuario responsable y lote asociado.
"""
from app.models import Movimiento
from app.services import inventario_service


def trazabilidad_alimento(alimento_id: int) -> dict:
    """Reconstruye la trazabilidad completa de un alimento."""
    alimento = _obtener_alimento(alimento_id)
    movimientos = (
        Movimiento.query.filter_by(alimento_id=alimento_id)
        .order_by(Movimiento.fecha.desc())
        .all()
    )
    resumen = inventario_service.resumen_por_alimento(alimento)
    return {
        "alimento": alimento,
        "movimientos": movimientos,
        "total_entradas": resumen["entradas"],
        "total_salidas": resumen["salidas"],
    }


def _obtener_alimento(alimento_id: int):
    from app.extensions import db
    from app.models import Alimento

    alimento = db.session.get(Alimento, alimento_id)
    if alimento is None:
        raise inventario_service.ErrorInventario("El alimento no existe.")
    return alimento