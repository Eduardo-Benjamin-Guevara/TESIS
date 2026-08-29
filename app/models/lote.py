"""Modelo de Lote de alimento.

Cada lote corresponde a una partida de un alimento con su fecha de
vencimiento. Permite conocer el stock disponible por lote y cuándo vence,
base del sistema de alertas (volumen por fecha de vencimiento).
"""
from decimal import Decimal

from app.extensions import db
from app.utils.timezone import utcnow


class Lote(db.Model):
    """Representa un lote de un alimento con su fecha de vencimiento."""

    __tablename__ = "lotes"

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(30), nullable=True, unique=True, index=True)
    alimento_id = db.Column(
        db.Integer, db.ForeignKey("alimentos.id"), nullable=False, index=True
    )
    fecha_ingreso = db.Column(db.Date, nullable=True)
    fecha_vencimiento = db.Column(db.Date, nullable=False, index=True)
    cantidad = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    activo = db.Column(db.Boolean, nullable=False, default=True)
    fecha_creacion = db.Column(db.DateTime, nullable=False, default=utcnow)

    alimento = db.relationship("Alimento", back_populates="lotes")

    @property
    def vencido(self) -> bool:
        return self.fecha_vencimiento is not None and _fecha_hoy() > self.fecha_vencimiento

    @property
    def dias_para_vencer(self) -> int:
        if self.fecha_vencimiento is None:
            return 0
        delta = (self.fecha_vencimiento - _fecha_hoy()).days
        return max(delta, 0)

    def __repr__(self):
        return f"<Lote {self.codigo or self.id} Alimento {self.alimento_id} vence {self.fecha_vencimiento}>"


def _fecha_hoy():
    from datetime import date
    return date.today()
