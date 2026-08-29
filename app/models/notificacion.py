"""Modelo de notificaciones leídas.

Registra qué alertas ha confirmado/leído cada usuario. Como las alertas se
calculan de forma derivada (stock bajo y lotes próximos a vencer), esta tabla
guarda el reconocimiento del usuario (tipo de alerta + referencia) para poder
distinguir entre "nuevas" y "ya leídas" sin duplicar el estado del inventario.
"""
from app.extensions import db
from app.utils.timezone import utcnow


class NotificacionLeida(db.Model):
    """Marca que un usuario leyó una alerta concreta."""

    __tablename__ = "notificaciones_leidas"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(
        db.Integer, db.ForeignKey("usuarios.id"), nullable=False, index=True
    )
    # tipo: 'vencimiento' | 'stock'; referencia: id del lote o del alimento
    tipo = db.Column(db.String(20), nullable=False)
    referencia_id = db.Column(db.Integer, nullable=False)
    leida_at = db.Column(db.DateTime, nullable=False, default=utcnow)

    usuario = db.relationship("Usuario", backref="notificaciones_leidas")

    __table_args__ = (
        db.UniqueConstraint(
            "usuario_id", "tipo", "referencia_id", name="uq_notificacion_leida"
        ),
    )

    def __repr__(self):
        return f"<NotificacionLeida {self.usuario_id} {self.tipo}:{self.referencia_id}>"
