"""Servicio de lotes y fechas de vencimiento."""
from datetime import date

from app.extensions import db
from app.models.alimento import Alimento
from app.models.lote import Lote


class ErrorNegocioLote(Exception):
    """Error de regla de negocio para lotes."""


def listar(filtro: str = "", incluir_inactivos: bool = False) -> list[Lote]:
    """Consulta lotes con búsqueda opcional por alimento o código de lote."""
    query = Lote.query
    if not incluir_inactivos:
        query = query.filter(Lote.activo.is_(True))
    if filtro:
        patron = f"%{filtro.strip()}%"
        query = query.join(Alimento).filter(
            db.or_(Alimento.nombre.ilike(patron), Alimento.codigo.ilike(patron), Lote.codigo.ilike(patron))
        )
    return query.order_by(Lote.fecha_vencimiento.asc()).all()


def obtener(lote_id: int) -> Lote | None:
    return db.session.get(Lote, lote_id)


def lote_codigo_existe(codigo: str, excluir_id: int | None = None) -> bool:
    if not codigo:
        return False
    query = Lote.query.filter_by(codigo=codigo.strip().upper())
    if excluir_id is not None:
        query = query.filter(Lote.id != excluir_id)
    return db.session.query(query.exists()).scalar()


def crear(
    alimento_id: int,
    fecha_vencimiento,
    cantidad,
    codigo: str | None = None,
    fecha_ingreso=None,
) -> Lote:
    """Crea un lote para un alimento y actualiza el stock de este."""
    alimento = db.session.get(Alimento, alimento_id)
    if alimento is None:
        raise ErrorNegocioLote("El alimento seleccionado no existe.")

    if fecha_vencimiento is None:
        raise ErrorNegocioLote("La fecha de vencimiento es obligatoria.")
    try:
        cantidad_val = float(cantidad or 0)
    except (TypeError, ValueError):
        raise ErrorNegocioLote("La cantidad debe ser un número válido.")
    if cantidad_val <= 0:
        raise ErrorNegocioLote("La cantidad del lote debe ser mayor que cero.")

    codigo_norm = (codigo or "").strip().upper() or None
    if codigo_norm and lote_codigo_existe(codigo_norm):
        raise ErrorNegocioLote("Ya existe un lote con ese código.")

    lote = Lote(
        codigo=codigo_norm,
        alimento_id=alimento_id,
        fecha_vencimiento=fecha_vencimiento,
        fecha_ingreso=fecha_ingreso or date.today(),
        cantidad=cantidad_val,
    )
    db.session.add(lote)

    # Actualizar stock del alimento sumando la cantidad del lote
    alimento.stock_actual = float(alimento.stock_actual or 0) + cantidad_val
    db.session.commit()
    return lote


def actualizar(
    lote: Lote,
    codigo: str | None,
    fecha_vencimiento,
    cantidad,
) -> Lote:
    """Actualiza un lote. Si cambia la cantidad, ajusta el stock del alimento."""
    if fecha_vencimiento is None:
        raise ErrorNegocioLote("La fecha de vencimiento es obligatoria.")
    try:
        cantidad_val = float(cantidad or 0)
    except (TypeError, ValueError):
        raise ErrorNegocioLote("La cantidad debe ser un número válido.")
    if cantidad_val < 0:
        raise ErrorNegocioLote("La cantidad no puede ser negativa.")

    codigo_norm = (codigo or "").strip().upper() or None
    if codigo_norm and lote_codigo_existe(codigo_norm, excluir_id=lote.id):
        raise ErrorNegocioLote("Ya existe un lote con ese código.")

    # Ajustar stock por diferencia de cantidad
    diferencia = cantidad_val - float(lote.cantidad or 0)
    lote.codigo = codigo_norm
    lote.fecha_vencimiento = fecha_vencimiento
    lote.cantidad = cantidad_val
    lote.alimento.stock_actual = float(lote.alimento.stock_actual or 0) + diferencia
    db.session.commit()
    return lote


def alternar_estado(lote: Lote) -> Lote:
    """Activa/desactiva (baja lógica) un lote sin tocar stock (la gestión de
    stock vía lotes se detalla en el módulo de inventario)."""
    lote.activo = not lote.activo
    db.session.commit()
    return lote


def listar_por_alimento(alimento_id: int, incluir_inactivos: bool = False) -> list[Lote]:
    query = Lote.query.filter_by(alimento_id=alimento_id)
    if not incluir_inactivos:
        query = query.filter(Lote.activo.is_(True))
    return query.order_by(Lote.fecha_vencimiento.asc()).all()
