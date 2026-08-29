"""Rutas de gestión de inventario: entradas, salidas, disponibilidad e historial."""
from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from flask_wtf import FlaskForm
from wtforms import DecimalField, SelectField, StringField, TextAreaField
from wtforms.validators import InputRequired, NumberRange, Optional

from app.models.movimiento import TipoMovimiento
from app.services import (
    alimento_service,
    categoria_service,
    inventario_service,
    lote_service,
)
from app.services.inventario_service import ErrorInventario
from app.utils.decorators import rol_requerido

bp = Blueprint("inventario", __name__, url_prefix="/inventario")


class MovimientoForm(FlaskForm):
    alimento = SelectField("Alimento", validators=[InputRequired()])
    cantidad = DecimalField(
        "Cantidad",
        validators=[InputRequired(), NumberRange(min=0)],
        render_kw={"placeholder": "0.00", "step": "0.01"},
        places=2,
    )
    lote = SelectField("Lote (opcional)", validators=[Optional()])
    motivo = TextAreaField(
        "Motivo / referencia",
        validators=[Optional()],
        render_kw={"rows": "3", "maxlength": "255"},
    )


def _opciones_alimentos():
    return [(str(a.id), f"{a.codigo} - {a.nombre}") for a in alimento_service.listar()]


def _opciones_lotes(alimento_id=None):
    opciones = [("", "Sin lote específico")]
    if alimento_id:
        for l in lote_service.listar_por_alimento(alimento_id):
            if l.activo and float(l.cantidad or 0) > 0:
                opciones.append(
                    (str(l.id), f"Lote {l.codigo or l.id} (vence {l.fecha_vencimiento}, {l.cantidad})")
                )
    return opciones


def _cargar_selecciones(form, alimento_id=None):
    form.alimento.choices = [("", "Seleccione...")] + _opciones_alimentos()
    form.lote.choices = _opciones_lotes(alimento_id)


def _ejecutar(tipo, form):
    try:
        if tipo == TipoMovimiento.ENTRADA:
            inventario_service.registrar_entrada(
                alimento_id=int(form.alimento.data),
                cantidad=form.cantidad.data,
                usuario=current_user,
                motivo=form.motivo.data,
                lote_id=int(form.lote.data) if form.lote.data else None,
            )
            flash("Entrada registrada y stock actualizado.", "success")
        else:
            inventario_service.registrar_salida(
                alimento_id=int(form.alimento.data),
                cantidad=form.cantidad.data,
                usuario=current_user,
                motivo=form.motivo.data,
                lote_id=int(form.lote.data) if form.lote.data else None,
            )
            flash("Salida registrada y stock actualizado.", "success")
        return True
    except ErrorInventario as e:
        flash(str(e), "danger")
        return False


@bp.route("/entradas/nueva", methods=["GET", "POST"])
@login_required
@rol_requerido("admin", "encargado")
def nueva_entrada():
    form = MovimientoForm()
    _cargar_selecciones(form)
    if request.method == "POST":
        form.alimento.choices = [("", "Seleccione...")] + _opciones_alimentos()
        alimento_id = request.form.get("alimento") or None
        form.lote.choices = _opciones_lotes(int(alimento_id) if alimento_id else None)
        if form.validate_on_submit() and _ejecutar(TipoMovimiento.ENTRADA, form):
            return redirect(url_for("inventario.historial"))
    return render_template("inventario/form.html", form=form, tipo="entrada",
                           titulo="Registrar entrada")


@bp.route("/salidas/nueva", methods=["GET", "POST"])
@login_required
@rol_requerido("admin", "encargado")
def nueva_salida():
    form = MovimientoForm()
    _cargar_selecciones(form)
    if request.method == "POST":
        form.alimento.choices = [("", "Seleccione...")] + _opciones_alimentos()
        alimento_id = request.form.get("alimento") or None
        form.lote.choices = _opciones_lotes(int(alimento_id) if alimento_id else None)
        if form.validate_on_submit() and _ejecutar(TipoMovimiento.SALIDA, form):
            return redirect(url_for("inventario.historial"))
    return render_template("inventario/form.html", form=form, tipo="salida",
                           titulo="Registrar salida")


@bp.route("/disponibilidad")
@login_required
def disponibilidad():
    filtro = request.args.get("q", "").strip()
    categoria_id = request.args.get("categoria", "").strip()
    alimentos = alimento_service.listar(filtro=filtro, categoria_id=categoria_id)
    # Enriquecer con disponibilidad por lote
    items = []
    for a in alimentos:
        total, lotes = inventario_service.disponibilidad(a.id)
        items.append({"alimento": a, "total": total, "lotes": lotes})
    return render_template(
        "inventario/disponibilidad.html",
        items=items,
        filtro=filtro,
        categoria_id=categoria_id,
        categorias=categoria_service.listar(),
    )


@bp.route("/alimento/<int:alimento_id>/lotes")
@login_required
def lotes_de_alimento(alimento_id):
    """Devuelve en JSON los lotes activos de un alimento (para el select dinámico)."""
    opciones = [{"id": "", "texto": "Sin lote específico"}]
    for l in lote_service.listar_por_alimento(alimento_id):
        if l.activo and float(l.cantidad or 0) > 0:
            opciones.append(
                {
                    "id": str(l.id),
                    "texto": f"Lote {l.codigo or l.id} (vence {l.fecha_vencimiento}, {l.cantidad})",
                }
            )
    return jsonify(opciones)


@bp.route("/historial")
@login_required
def historial():
    filtro = request.args.get("q", "").strip()
    tipo = request.args.get("tipo", "").strip()
    movimientos = inventario_service.listar_movimientos(filtro=filtro, tipo=tipo)
    return render_template(
        "inventario/historial.html",
        movimientos=movimientos,
        filtro=filtro,
        tipo=tipo,
    )
