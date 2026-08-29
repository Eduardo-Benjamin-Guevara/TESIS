"""Servicio de lógica de negocio para categorías de alimentos."""
from app.extensions import db
from app.models.categoria import Categoria


class ErrorNegocioCategoria(Exception):
    """Error de regla de negocio para categorías."""


def listar(incluir_inactivas: bool = False) -> list[Categoria]:
    query = Categoria.query
    if not incluir_inactivas:
        query = query.filter(Categoria.activo.is_(True))
    return query.order_by(Categoria.nombre.asc()).all()


def obtener(categoria_id: int) -> Categoria | None:
    return db.session.get(Categoria, categoria_id)


def nombre_existe(nombre: str, excluir_id: int | None = None) -> bool:
    nombre_norm = nombre.strip().lower()
    query = Categoria.query.filter(db.func.lower(Categoria.nombre) == nombre_norm)
    if excluir_id is not None:
        query = query.filter(Categoria.id != excluir_id)
    return db.session.query(query.exists()).scalar()


def crear(nombre: str, descripcion: str | None = None) -> Categoria:
    nombre_norm = nombre.strip()
    if not nombre_norm:
        raise ErrorNegocioCategoria("El nombre de la categoría es obligatorio.")
    if nombre_existe(nombre_norm):
        raise ErrorNegocioCategoria("Ya existe una categoría con ese nombre.")
    categoria = Categoria(nombre=nombre_norm.lower(), descripcion=(descripcion or "").strip() or None)
    db.session.add(categoria)
    db.session.commit()
    return categoria


def actualizar(categoria: Categoria, nombre: str, descripcion: str | None) -> Categoria:
    nombre_norm = nombre.strip()
    if not nombre_norm:
        raise ErrorNegocioCategoria("El nombre de la categoría es obligatorio.")
    if nombre_existe(nombre_norm, excluir_id=categoria.id):
        raise ErrorNegocioCategoria("Ya existe una categoría con ese nombre.")
    categoria.nombre = nombre_norm.lower()
    categoria.descripcion = (descripcion or "").strip() or None
    db.session.commit()
    return categoria


def alternar_estado(categoria: Categoria) -> Categoria:
    categoria.activo = not categoria.activo
    db.session.commit()
    return categoria


def contar() -> int:
    return Categoria.query.filter(Categoria.activo.is_(True)).count()
