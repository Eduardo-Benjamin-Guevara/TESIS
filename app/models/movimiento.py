"""Modelo de Movimiento de inventario.

Registra cada entrada o salida de stock de un alimento, dejando trazabilidad
de quién, cuándo y cuánto. El stock del alimento se actualiza mediante los
servicios de inventario al crear un movimiento.
"""
from app.extensions import db
from app.utils.timezone import utcnow


class TipoMovimiento:
    """Tipos de movimiento de inventario."""

    ENTRADA = "entrada"
    SALIDA = "salida"

    VALORES = [ENTRADA, SALIDA]


class Movimiento(db.Model):
    """Representa una entrada o salida de stock de un alimento."""

    __tablename__ = "movimientos"

    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(10), nullable=False, index=True)  # entrada | salida
    alimento_id = db.Column(
        db.Integer, db.ForeignKey("alimentos.id"), nullable=False, index=True
    )
    lote_id = db.Column(db.Integer, db.ForeignKey("lotes.id"), nullable=True)
    cantidad = db.Column(db.Numeric(12, 2), nullable=False)
    stock_resultante = db.Column(db.Numeric(12, 2), nullable=False)
    motivo = db.Column(db.String(255), nullable=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    fecha = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)

    # Relaciones
    alimento = db.relationship("Alimento", back_populates="movimientos")
    lote = db.relationship("Lote", back_populates="movimientos")
    usuario = db.relationship("Usuario", back_populates="movimientos")

    @property
    def es_entrada(self) -> bool:
        return self.tipo == TipoMovimiento.ENTRADA

    @property
    def es_salida(self) -> bool:
        return self.tipo == TipoMovimiento.SALIDA

    def __repr__(self):
        return f"<Movimiento {self.tipo} {self.cantidad} Alimento {self.alimento_id}>"
