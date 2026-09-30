"""Rutas del asistente inteligente (IA).

Expone la página del chat y un endpoint JSON que los clientes (widget, página
completa) consumen para enviar preguntas y recibir respuestas del asistente,
integrado (modelo entrenado) o externo (API configurada con IA_API_KEY).
"""
from flask import Blueprint, jsonify, render_template, request
from flask_login import login_required

from app.services.ia_service import clasificar, preguntar

bp = Blueprint("ia", __name__, url_prefix="/ia")


@bp.route("/")
@login_required
def index():
    """Página completa del asistente inteligente."""
    return render_template("ia/chat.html")


@bp.route("/api/preguntar", methods=["POST"])
@login_required
def preguntar_api():
    """Procesa una pregunta del usuario y devuelve la respuesta en JSON.

    Cuerpo: ``{"mensaje": "..."}``. Devuelve ``respuesta``, ``intencion``,
    ``confianza`` y ``origen`` (``"externa"`` o ``"entrenada"``).
    """
    datos = request.get_json(silent=True) or {}
    mensaje = (datos.get("mensaje") or "").strip()
    if not mensaje:
        return (
            jsonify(
                {
                    "error": "Debes escribir una pregunta.",
                    "respuesta": "",
                    "intencion": "",
                    "confianza": 0,
                    "origen": "",
                }
            ),
            400,
        )
    resultado = preguntar(mensaje)
    resultado["error"] = ""
    return jsonify(resultado)