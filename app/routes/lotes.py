"""Rutas de lotes: registro de fechas de vencimiento por alimento."""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import login_required
from flask_wtf import FlaskForm
from wtforms import DateField, DecimalField, SelectField, StringField
from wtforms.validators import DataRequired, InputRequired, NumberRange, Optional

from app.services import alimento_service, lote_service
from app.services.lote_service import ErrorNegocioLote
from app.utils.decorators import rol_requerido

bp = Blueprint("lotes", __name__, url_prefix="/lotes")


class LoteForm(FlaskForm):
    codigo = StringField(
        "Código del lote (opcional)",
        validators=[Optional()],
        render_kw={"placeholder": "Ej. LOTE-2026-001", "maxlength": "30"},
    )
    alimento = SelectField("Alimento", validators=[DataRequired()])
    fecha_vencimiento = DateField("Fecha de vencimiento", validators=[DataRequired()])
    fecha_ingreso = DateField("Fecha de ingreso", validators=[Optional()])
    cantidad = DecimalField(
        "Cantidad",
        validators=[InputRequired(), NumberRange(min=0)],
        render_kw={"placeholder": "0.00", "step": "0.01"},
        places=2,
    )


def _opciones_alimentos():
    return [(str(a.id), f"{a.codigo} - {a.nombre}") for a in alimento_service.listar()]


@bp.route("/")
@login_required
def index():
    filtro = request.args.get("q", "").strip()
    incluir_inactivos = request.args.get("inactivos", "").lower() in ("1", "true", "si")
    lotes = lote_service.listar(filtro=filtro, incluir_inactivos=incluir_inactivos)
    return render_template(
        "lotes/index.html",
        lotes=lotes,
        filtro=filtro,
        incluir_inactivos=incluir_inactivos,
    )


@bp.route("/nuevo", methods=["GET", "POST"])
@login_required
@rol_requerido("admin", "encargado")
def nuevo():
    form = LoteForm()
    form.alimento.choices = [("", "Seleccione...")] + _opciones_alimentos()
    if form.validate_on_submit():
        try:
            lote_service.crear(
                alimento_id=form.alimento.data,
                codigo=form.codigo.data,
                fecha_vencimiento=form.fecha_vencimiento.data,
                fecha_ingreso=form.fecha_ingreso.data,
                cantidad=form.cantidad.data,
            )
            flash("Lote registrado y stock actualizado.", "success")
            return redirect(url_for("lotes.index"))
        except ErrorNegocioLote as e:
            flash(str(e), "danger")
    return render_template("lotes/form.html", form=form, titulo="Registrar lote")


@bp.route("/<int:lote_id>/editar", methods=["GET", "POST"])
@login_required
@rol_requerido("admin", "encargado")
def editar(lote_id):
    lote = lote_service.obtener(lote_id)
    if lote is None:
        abort(404)

    form = LoteForm(obj=lote)
    form.alimento.choices = [("", "Seleccione...")] + _opciones_alimentos()
    if form.alimento.data is None:
        form.alimento.data = str(lote.alimento_id)

    if form.validate_on_submit():
        try:
            lote_service.actualizar(
                lote,
                codigo=form.codigo.data,
                fecha_vencimiento=form.fecha_vencimiento.data,
                cantidad=form.cantidad.data,
            )
            flash("Lote actualizado correctamente.", "success")
            return redirect(url_for("lotes.index"))
        except ErrorNegocioLote as e:
            flash(str(e), "danger")

    return render_template("lotes/form.html", form=form, titulo="Editar lote", lote=lote)


@bp.post("/<int:lote_id>/estado")
@login_required
@rol_requerido("admin")
def cambiar_estado(lote_id):
    lote = lote_service.obtener(lote_id)
    if lote is None:
        abort(404)
    lote_service.alternar_estado(lote)
    estado = "activado" if lote.activo else "desactivado"
    flash(f"Lote {estado}.", "success")
    return redirect(url_for("lotes.index"))
