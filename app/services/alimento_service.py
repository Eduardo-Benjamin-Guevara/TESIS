"""Servicio de lógica de negocio para la gestión de alimentos.

Encapsula las reglas del dominio (código único, categoría válida, filtros,
estado activo/inactivo) para que las rutas sean delgadas y reutilizables.
"""
from app.extensions import db
from app.models.categoria import Categoria
from app.models.alimento import Alimento


class ErrorNegocio(Exception):
    """Error de regla de negocio que se traduce en un mensaje al usuario."""


def _repo_codigo_duplicado(codigo: str, excluir_id: int | None = None) -> bool:
    query = Alimento.query.filter_by(codigo=codigo)
    if excluir_id is not None:
        query = query.filter(Alimento.id != excluir_id)
    return db.session.query(query.exists()).scalar()


def codigo_en_uso(codigo: str, excluir_id: int | None = None) -> bool:
    """Indica si el código ya está registrado en otro alimento."""
    return _repo_codigo_duplicado(codigo, excluir_id)


def _validar_categoria(categoria_id) -> Categoria:
    if not categoria_id:
        raise ErrorNegocio("Debes seleccionar una categoría.")
    cat = db.session.get(Categoria, int(categoria_id))
    if cat is None:
        raise ErrorNegocio("La categoría seleccionada no existe.")
    return cat


def crear_alimento(
    codigo: str,
    nombre: str,
    categoria_id: int,
    unidad_medida: str,
    descripcion: str | None,
    stock_actual,
    stock_minimo,
) -> Alimento:
    """Crea un nuevo alimento validando sus reglas de negocio."""
    codigo_norm = Alimento.normalizar_codigo(codigo)
    if _repo_codigo_duplicado(codigo_norm):
        raise ErrorNegocio("Ya existe un alimento con ese código.")
    _validar_categoria(categoria_id)

    alimento = Alimento(
        codigo=codigo_norm,
        nombre=nombre.strip(),
        categoria_id=int(categoria_id),
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
    categoria_id: int,
    unidad_medida: str,
    descripcion: str | None,
    stock_actual,
    stock_minimo,
) -> Alimento:
    """Actualiza los datos de un alimento validando reglas de negocio."""
    codigo_norm = Alimento.normalizar_codigo(codigo)
    if _repo_codigo_duplicado(codigo_norm, excluir_id=alimento.id):
        raise ErrorNegocio("Ya existe otro alimento con ese código.")
    _validar_categoria(categoria_id)

    alimento.codigo = codigo_norm
    alimento.nombre = nombre.strip()
    alimento.categoria_id = int(categoria_id)
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


def obtener(alimento_id: int) -> Alimento | None:
    return db.session.get(Alimento, alimento_id)


def listar(filtro: str = "", categoria_id: str = "", incluir_inactivos: bool = False) -> list[Alimento]:
    """Consulta alimentos con búsqueda y filtrado opcional.

    - `filtro`: texto que coincide con código o nombre.
    - `categoria_id`: id exacto de la categoría.
    - `incluir_inactivos`: si es True, muestra también los inactivos.
    """
    query = Alimento.query
    if not incluir_inactivos:
        query = query.filter(Alimento.activo.is_(True))
    if categoria_id:
        query = query.filter(Alimento.categoria_id == int(categoria_id))
    if filtro:
        patron = f"%{filtro.strip()}%"
        query = query.filter(
            db.or_(Alimento.codigo.ilike(patron), Alimento.nombre.ilike(patron))
        )
    return query.order_by(Alimento.codigo.asc()).all()


def contar_total() -> int:
    """Número de alimentos activos (para el panel principal)."""
    return Alimento.query.filter(Alimento.activo.is_(True)).count()
