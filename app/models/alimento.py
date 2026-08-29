"""Modelo de Alimento.

Representa un alimento del inventario. Cataloga las cantidades de stock y se
relaciona con su categoría y con los lotes (cada uno con su fecha de
vencimiento). Las entradas y salidas (movimientos) se registran en el módulo
de inventario.
"""
import re

from app.extensions import db
from app.utils.timezone import utcnow

# Patrón de referencia para el código del alimento (3-20 alfanuméricos)
PATRON_CODIGO = re.compile(r"^[A-Z0-9]{3,20}$")


class Alimento(db.Model):
    """Representa un alimento registrado en el inventario."""

    __tablename__ = "alimentos"

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False, index=True)
    nombre = db.Column(db.String(150), nullable=False)
    categoria_id = db.Column(
        db.Integer, db.ForeignKey("categorias.id"), nullable=True, index=True
    )
    unidad_medida = db.Column(db.String(30), nullable=False)
    descripcion = db.Column(db.String(500), nullable=True)
    stock_actual = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    stock_minimo = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    activo = db.Column(db.Boolean, nullable=False, default=True)
    fecha_creacion = db.Column(db.DateTime, nullable=False, default=utcnow)
    fecha_actualizacion = db.Column(
        db.DateTime, nullable=False, default=utcnow, onupdate=utcnow
    )

    # Relaciones
    categoria_rel = db.relationship("Categoria", back_populates="alimentos")
    lotes = db.relationship(
        "Lote", back_populates="alimento", lazy="select",
        order_by="Lote.fecha_vencimiento",
    )

    # -- Validación de datos -------------------------------------------
    @staticmethod
    def normalizar_codigo(codigo: str) -> str:
        """Devuelve el código en mayúsculas y sin espacios."""
        return codigo.strip().upper().replace(" ", "")

    # -- Consultas de stock --------------------------------------------
    @property
    def stock_bajo(self) -> bool:
        """Indica si el stock actual está por debajo del mínimo."""
        return self.stock_actual is not None and self.stock_minimo is not None and (
            float(self.stock_actual) <= float(self.stock_minimo)
        )

    @property
    def categoria(self) -> str:
        """Nombre de la categoría (compatibilidad con plantillas)."""
        return self.categoria_rel.nombre if self.categoria_rel else ""

    @property
    def proximo_vencimiento(self):
        """Primera fecha de vencimiento de los lotes activos (o None)."""
        activos = [l for l in self.lotes if l.activo]
        if not activos:
            return None
        return min(activos, key=lambda l: l.fecha_vencimiento)

    def __repr__(self):
        return f"<Alimento {self.codigo} - {self.nombre}>"
