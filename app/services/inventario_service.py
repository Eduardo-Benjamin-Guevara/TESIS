"""Servicio de inventario: entradas, salidas, stock y disponibilidad.

Registra movimientos de stock y actualiza el inventario de forma
transaccional: una entrada suma y una salida resta (validando que haya
stock suficiente). Cada movimiento queda en el historial.
"""
from app.extensions import db
from app.models.alimento import Alimento
from app.models.lote import Lote
from app.models.movimiento import Movimiento, TipoMovimiento


class ErrorInventario(Exception):
    """Error de regla de negocio de inventario (se muestra al usuario)."""


def _cantidad_valida(cantidad) -> float:
    try:
        valor = float(cantidad or 0)
    except (TypeError, ValueError):
        raise ErrorInventario("La cantidad debe ser un número válido.")
    if valor <= 0:
        raise ErrorInventario("La cantidad debe ser mayor que cero.")
    return valor


def _validar_producto(alimento_id: int) -> Alimento:
    alimento = db.session.get(Alimento, alimento_id)
    if alimento is None:
        raise ErrorInventario("El alimento seleccionado no existe.")
    return alimento


def registrar_entrada(
    alimento_id: int,
    cantidad,
    usuario,
    motivo: str | None = None,
    lote_id: int | None = None,
) -> Movimiento:
    """Registra una entrada y aumenta el stock del alimento."""
    alimento = _validar_producto(alimento_id)
    cantidad_val = _cantidad_valida(cantidad)

    lote = None
    if lote_id:
        lote = db.session.get(Lote, lote_id)
        if lote is None or lote.alimento_id != alimento_id:
            raise ErrorInventario("El lote seleccionado no pertenece a este alimento.")
        lote.cantidad = float(lote.cantidad or 0) + cantidad_val

    nuevo_stock = float(alimento.stock_actual or 0) + cantidad_val
    alimento.stock_actual = nuevo_stock

    movimiento = Movimiento(
        tipo=TipoMovimiento.ENTRADA,
        alimento_id=alimento_id,
        lote_id=lote_id,
        cantidad=cantidad_val,
        stock_resultante=nuevo_stock,
        motivo=(motivo or "").strip() or None,
        usuario_id=usuario.id,
    )
    db.session.add(movimiento)
    db.session.commit()
    return movimiento


def registrar_salida(
    alimento_id: int,
    cantidad,
    usuario,
    motivo: str | None = None,
    lote_id: int | None = None,
) -> Movimiento:
    """Registra una salida y disminuye el stock validando disponibilidad."""
    alimento = _validar_producto(alimento_id)
    cantidad_val = _cantidad_valida(cantidad)

    stock_actual = float(alimento.stock_actual or 0)
    if cantidad_val > stock_actual:
        raise ErrorInventario(
            f"Stock insuficiente. Disponible: {stock_actual} {alimento.unidad_medida}."
        )

    lote = None
    if lote_id:
        lote = db.session.get(Lote, lote_id)
        if lote is None or lote.alimento_id != alimento_id:
            raise ErrorInventario("El lote seleccionado no pertenece a este alimento.")
        if float(lote.cantidad or 0) < cantidad_val:
            raise ErrorInventario(
                f"Cantidad insuficiente en el lote seleccionado (disponible: {float(lote.cantidad or 0)})."
            )
        lote.cantidad = float(lote.cantidad or 0) - cantidad_val

    nuevo_stock = stock_actual - cantidad_val
    alimento.stock_actual = nuevo_stock

    movimiento = Movimiento(
        tipo=TipoMovimiento.SALIDA,
        alimento_id=alimento_id,
        lote_id=lote_id,
        cantidad=cantidad_val,
        stock_resultante=nuevo_stock,
        motivo=(motivo or "").strip() or None,
        usuario_id=usuario.id,
    )
    db.session.add(movimiento)
    db.session.commit()
    return movimiento


def disponibilidad(alimento_id: int):
    """Devuelve la cantidad disponible de un alimento.

    Retorna una tupla (stock_total, lotes_activos). Si no hay lotes, la
    disponibilidad equivale al campo stock_actual.
    """
    alimento = _validar_producto(alimento_id)
    lotes = [l for l in alimento.lotes if l.activo and float(l.cantidad or 0) > 0]
    return float(alimento.stock_actual or 0), lotes


def stock_disponible(alimento) -> float:
    """Devuelve el stock disponible (float) de un alimento."""
    return float(alimento.stock_actual or 0)


def listar_movimientos(
    filtro: str = "",
    tipo: str = "",
    desde=None,
    hasta=None,
    limit: int | None = None,
) -> list[Movimiento]:
    """Consulta el historial de movimientos con filtros opcionales.

    - `filtro`: coincide con código o nombre del alimento.
    - `tipo`: 'entrada' o 'salida'.
    - `desde`/`hasta`: rango de fechas.
    """
    query = Movimiento.query
    if tipo:
        query = query.filter(Movimiento.tipo == tipo)
    if filtro:
        patron = f"%{filtro.strip()}%"
        query = query.join(Alimento, Alimento.id == Movimiento.alimento_id).filter(
            db.or_(Alimento.codigo.ilike(patron), Alimento.nombre.ilike(patron))
        )
    if desde:
        query = query.filter(Movimiento.fecha >= desde)
    if hasta:
        query = query.filter(Movimiento.fecha <= hasta)
    query = query.order_by(Movimiento.fecha.desc())
    if limit:
        query = query.limit(limit)
    return query.all()


def resumen_por_alimento(alimento, limit: int | None = None) -> dict:
    """Resumen de entradas y salidas de un alimento."""
    entradas = sum(
        float(m.cantidad)
        for m in Movimiento.query.filter_by(
            alimento_id=alimento.id, tipo=TipoMovimiento.ENTRADA
        ).all()
    )
    salidas = sum(
        float(m.cantidad)
        for m in Movimiento.query.filter_by(
            alimento_id=alimento.id, tipo=TipoMovimiento.SALIDA
        ).all()
    )
    return {"entradas": entradas, "salidas": salidas}
