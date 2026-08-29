"""Modelo de Alimento.

El diseño queda preparado para incorporar en las siguientes versiones:
lotes, fechas de vencimiento, proveedores, entradas/salidas, responsables,
fotografías, códigos QR y trazabilidad. Por ahora se mantiene una entidad
central con campos esenciales de stock y auditoría.
"""
import re

from app.extensions import db
from app.utils.timezone import utcnow

# Patrones normalizados para el código del alimento
PATRON_CODIGO = re.compile(r"^[A-Z0-9]{3,20}$")


class CategoriaAlimento:
    """Categorías disponibles para clasificar los alimentos."""

    GRANOS = "granos"
    LACTEOS = "lacteos"
    CARNES = "carnes"
    FRUTAS = "frutas"
    VERDURAS = "verduras"
    ABARROTES = "abarrotes"
    BEBIDAS = "bebidas"
    OTROS = "otros"

    VALORES = [
        GRANOS,
        LACTEOS,
        CARNES,
        FRUTAS,
        VERDURAS,
        ABARROTES,
        BEBIDAS,
        OTROS,
    ]


class Alimento(db.Model):
    """Representa un alimento registrado en el inventario."""

    __tablename__ = "alimentos"

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False, index=True)
    nombre = db.Column(db.String(150), nullable=False)
    categoria = db.Column(db.String(30), nullable=False)
    unidad_medida = db.Column(db.String(30), nullable=False)
    descripcion = db.Column(db.String(500), nullable=True)
    stock_actual = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    stock_minimo = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    activo = db.Column(db.Boolean, nullable=False, default=True)
    fecha_creacion = db.Column(db.DateTime, nullable=False, default=utcnow)
    fecha_actualizacion = db.Column(
        db.DateTime, nullable=False, default=utcnow, onupdate=utcnow
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

    def __repr__(self):
        return f"<Alimento {self.codigo} - {self.nombre}>"
