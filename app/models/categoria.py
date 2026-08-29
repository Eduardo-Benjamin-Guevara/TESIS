"""Modelo de Categoria alimentaria.

Registro gestionable de categorías de alimentos. Reemplaza la lista fija de
categorías de la versión 1, permitiendo crear nuevas categorías desde la
interfaz sin modificar el código.
"""
from app.extensions import db
from app.utils.timezone import utcnow

# Categorías por defecto con las que se siembra el sistema
CATEGORIAS_DEFECTO = [
    "granos",
    "lacteos",
    "carnes",
    "frutas",
    "verduras",
    "abarrotes",
    "bebidas",
    "otros",
]


class Categoria(db.Model):
    """Representa una categoría de alimentos."""

    __tablename__ = "categorias"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False, index=True)
    descripcion = db.Column(db.String(255), nullable=True)
    activo = db.Column(db.Boolean, nullable=False, default=True)
    fecha_creacion = db.Column(db.DateTime, nullable=False, default=utcnow)

    # Relación inversa con Alimento (definida en alimento.py)
    alimentos = db.relationship("Alimento", back_populates="categoria_rel", lazy="dynamic")

    @property
    def total_alimentos(self) -> int:
        return self.alimentos.filter_by(activo=True).count()

    def __repr__(self):
        return f"<Categoria {self.nombre}>"
