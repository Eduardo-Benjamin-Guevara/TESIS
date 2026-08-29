"""Rutas del centro de notificaciones.

Expone un endpoint JSON que la campana del topbar consulta para mostrar las
notificaciones de alertas (próximos a vencer y stock bajo) con su estado de
lectura, y permite marcar todas como leídas.
"""
from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app.services import notificaciones_service

bp = Blueprint("notificaciones", __name__, url_prefix="/notificaciones")


@bp.route("/")
@login_required
def listar():
    """Devuelve las notificaciones del usuario autenticado en JSON."""
    datos = notificaciones_service.notificaciones_usuario(current_user)
    return jsonify(
        {"items": datos["items"], "no_leidas": datos["no_leidas"], "total": datos["total"]}
    )


@bp.route("/leidas", methods=["POST"])
@login_required
def marcar_leidas():
    """Marca todas las notificaciones del usuario como leídas."""
    nuevas = notificaciones_service.marcar_todas_como_leidas(current_user)
    return jsonify({"ok": True, "marcadas": nuevas})
