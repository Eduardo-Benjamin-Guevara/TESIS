"""Servicio de lógica de negocio para la gestión de alimentos.

Encapsula las reglas del dominio (código único, validaciones, filtros,
estado activo/inactivo) para que las rutas sean delgadas y reutilizables.
"""
from flask import current_app

from app.extensions import db
from app.models.alimento import Alimento, CategoriaAlimento


class ErrorNegocio(Exception):
    """Error de regla de negocio que se traduce en un mensaje al usuario."""


def validar_codigo_unico(codigo: str, excluir_id: int | None = None) -> str | None:
    """Valida el código normalizado.

    Devuelve un mensaje de error o None si es válido.
    """
    codigo_normalizado = Alimento.normalizar_codigo(codigo)
    if not codigo_normalizado:
        return "El código del alimento es obligatorio."
    if not (3 <= len(codigo_normalizado) <= 20):
        return "El código debe tener entre 3 y 20 caracteres."
    # Debe ser alfanumérico
    if not codigo_normalizado.isalnum():
        return "El código solo puede contener letras y números."
    return None


def _repo_codigo_duplicado(codigo: str, excluir_id: int | None = None) -> bool:
    query = Alimento.query.filter_by(codigo=codigo)
    if excluir_id is not None:
        query = query.filter(Alimento.id != excluir_id)
    return db.session.query(query.exists()).scalar()


def codigo_en_uso(codigo: str, excluir_id: int | None = None) -> bool:
    """Indica si el código ya está registrado en otro alimento activo."""
    return _repo_codigo_duplicado(codigo, excluir_id)


def crear_alimento(
    codigo: str,
    nombre: str,
    categoria: str,
    unidad_medida: str,
    descripcion: str | None,
    stock_actual,
    stock_minimo,
) -> Alimento:
    """Crea un nuevo alimento validando sus reglas de negocio."""
    codigo_norm = Alimento.normalizar_codigo(codigo)
    if _repo_codigo_duplicado(codigo_norm):
        raise ErrorNegocio("Ya existe un alimento con ese código.")
    if categoria not in CategoriaAlimento.VALORES:
        raise ErrorNegocio("La categoría seleccionada no es válida.")

    alimento = Alimento(
        codigo=codigo_norm,
        nombre=nombre.strip(),
        categoria=categoria,
        unidad_medida=unidad_medida.strip(),
        descripcion=(descripcion or "").strip() or None,
        stock_actual=float(stock_actual or 0),
        stock_minimo=float(stock_minimo or 0),
    )
    db.session.add(alimento)
    db.session.commit()
    return alimento


def actualizar_alimento(
    alimento: Alimento,
    codigo: str,
    nombre: str,
    categoria: str,
    unidad_medida: str,
    descripcion: str | None,
    stock_actual,
    stock_minimo,
) -> Alimento:
    """Actualiza los datos de un alimento validando reglas de negocio."""
    codigo_norm = Alimento.normalizar_codigo(codigo)
    if _repo_codigo_duplicado(codigo_norm, excluir_id=alimento.id):
        raise ErrorNegocio("Ya existe otro alimento con ese código.")
    if categoria not in CategoriaAlimento.VALORES:
        raise ErrorNegocio("La categoría seleccionada no es válida.")

    alimento.codigo = codigo_norm
    alimento.nombre = nombre.strip()
    alimento.categoria = categoria
    alimento.unidad_medida = unidad_medida.strip()
    alimento.descripcion = (descripcion or "").strip() or None
    alimento.stock_actual = float(stock_actual or 0)
    alimento.stock_minimo = float(stock_minimo or 0)
    db.session.commit()
    return alimento


def alternar_estado(alimento: Alimento) -> Alimento:
    """Activa/desactiva (eliminación lógica) un alimento."""
    alimento.activo = not alimento.activo
    db.session.commit()
    return alimento


def obtener(id: int) -> Alimento | None:
    return db.session.get(Alimento, id)


def listar(filtro: str = "", categoria: str = "", incluir_inactivos: bool = False) -> list[Alimento]:
    """Consulta alimentos con búsqueda y filtrado opcional.

    - `filtro`: texto que coincide con código o nombre.
    - `categoria`: categoría exacta.
    - `incluir_inactivos`: si es True, muestra también los inactivos.
    """
    query = Alimento.query
    if not incluir_inactivos:
        query = query.filter(Alimento.activo.is_(True))
    if categoria:
        query = query.filter(Alimento.categoria == categoria)
    if filtro:
        patron = f"%{filtro.strip()}%"
        query = query.filter(
            db.or_(Alimento.codigo.ilike(patron), Alimento.nombre.ilike(patron))
        )
    return query.order_by(Alimento.codigo.asc()).all()


def contar_total() -> int:
    """Número de alimentos activos (para el panel principal)."""
    return Alimento.query.filter(Alimento.activo.is_(True)).count()
