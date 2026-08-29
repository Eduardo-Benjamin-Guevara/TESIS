"""Rutas del CRUD de alimentos."""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import login_required
from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DecimalField,
    SelectField,
    StringField,
    TextAreaField,
)
from wtforms.validators import DataRequired, NumberRange, Optional

from app.models.alimento import CategoriaAlimento
from app.services import alimento_service
from app.services.alimento_service import ErrorNegocio
from app.utils.decorators import rol_requerido

bp = Blueprint("alimentos", __name__, url_prefix="/alimentos")


class AlimentoForm(FlaskForm):
    codigo = StringField(
        "Código",
        validators=[DataRequired()],
        render_kw={"placeholder": "Ej. ARROZ001", "maxlength": "20"},
    )
    nombre = StringField(
        "Nombre del alimento",
        validators=[DataRequired()],
        render_kw={"placeholder": "Ej. Arroz extra", "maxlength": "150"},
    )
    categoria = SelectField(
        "Categoría",
        choices=[("", "Seleccione...")] + [(c, c.capitalize()) for c in CategoriaAlimento.VALORES],
        validators=[DataRequired()],
    )
    unidad_medida = StringField(
        "Unidad de medida",
        validators=[DataRequired()],
        render_kw={"placeholder": "Ej. kg, g, unidad, litro", "maxlength": "30"},
    )
    stock_actual = DecimalField(
        "Stock actual",
        validators=[DataRequired(), NumberRange(min=0)],
        render_kw={"placeholder": "0.00", "step": "0.01"},
        places=2,
    )
    stock_minimo = DecimalField(
        "Stock mínimo",
        validators=[DataRequired(), NumberRange(min=0)],
        render_kw={"placeholder": "0.00", "step": "0.01"},
        places=2,
    )
    descripcion = TextAreaField(
        "Descripción",
        validators=[Optional()],
        render_kw={"rows": "3", "maxlength": "500"},
    )


@bp.route("/")
@login_required
def index():
    """Listado y búsqueda de alimentos."""
    filtro = request.args.get("q", "").strip()
    categoria = request.args.get("categoria", "").strip()
    incluir_inactivos = request.args.get("inactivos", "").lower() in ("1", "true", "si")

    alimentos = alimento_service.listar(
        filtro=filtro, categoria=categoria, incluir_inactivos=incluir_inactivos
    )
    return render_template(
        "alimentos/index.html",
        alimentos=alimentos,
        filtro=filtro,
        categoria=categoria,
        incluir_inactivos=incluir_inactivos,
    )


@bp.route("/nuevo", methods=["GET", "POST"])
@login_required
@rol_requerido("admin", "encargado")
def nuevo():
    form = AlimentoForm()
    if form.validate_on_submit():
        try:
            alimento_service.crear_alimento(
                codigo=form.codigo.data,
                nombre=form.nombre.data,
                categoria=form.categoria.data,
                unidad_medida=form.unidad_medida.data,
                descripcion=form.descripcion.data,
                stock_actual=form.stock_actual.data,
                stock_minimo=form.stock_minimo.data,
            )
            flash("Alimento registrado correctamente.", "success")
            return redirect(url_for("alimentos.index"))
        except ErrorNegocio as e:
            flash(str(e), "danger")
    return render_template("alimentos/form.html", form=form, titulo="Registrar alimento")


@bp.route("/<int:alimento_id>/editar", methods=["GET", "POST"])
@login_required
@rol_requerido("admin", "encargado")
def editar(alimento_id):
    alimento = alimento_service.obtener(alimento_id)
    if alimento is None:
        abort(404)

    form = AlimentoForm(obj=alimento)
    if form.validate_on_submit():
        try:
            alimento_service.actualizar_alimento(
                alimento,
                codigo=form.codigo.data,
                nombre=form.nombre.data,
                categoria=form.categoria.data,
                unidad_medida=form.unidad_medida.data,
                descripcion=form.descripcion.data,
                stock_actual=form.stock_actual.data,
                stock_minimo=form.stock_minimo.data,
            )
            flash("Alimento actualizado correctamente.", "success")
            return redirect(url_for("alimentos.index"))
        except ErrorNegocio as e:
            flash(str(e), "danger")

    return render_template(
        "alimentos/form.html", form=form, titulo="Editar alimento", alimento=alimento
    )


@bp.route("/<int:alimento_id>")
@login_required
def detalle(alimento_id):
    alimento = alimento_service.obtener(alimento_id)
    if alimento is None:
        abort(404)
    return render_template("alimentos/detalle.html", alimento=alimento)


@bp.post("/<int:alimento_id>/estado")
@login_required
@rol_requerido("admin")
def cambiar_estado(alimento_id):
    alimento = alimento_service.obtener(alimento_id)
    if alimento is None:
        abort(404)
    alimento_service.alternar_estado(alimento)
    if alimento.activo:
        flash("Alimento activado.", "success")
    else:
        flash("Alimento desactivado (eliminación lógica).", "info")
    return redirect(url_for("alimentos.index"))
