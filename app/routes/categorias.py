"""Rutas del CRUD de categorías de alimentos."""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import login_required
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired, Optional

from app.services import categoria_service
from app.services.categoria_service import ErrorNegocioCategoria
from app.utils.decorators import rol_requerido

bp = Blueprint("categorias", __name__, url_prefix="/categorias")


class CategoriaForm(FlaskForm):
    nombre = StringField(
        "Nombre",
        validators=[DataRequired()],
        render_kw={"placeholder": "Ej. verduras", "maxlength": "50"},
    )
    descripcion = TextAreaField(
        "Descripción",
        validators=[Optional()],
        render_kw={"rows": "3", "maxlength": "255"},
    )


@bp.route("/")
@login_required
def index():
    incluir_inactivas = request.args.get("inactivas", "").lower() in ("1", "true", "si")
    categorias = categoria_service.listar(incluir_inactivas=incluir_inactivas)
    return render_template(
        "categorias/index.html",
        categorias=categorias,
        incluir_inactivas=incluir_inactivas,
    )


@bp.route("/nuevo", methods=["GET", "POST"])
@login_required
@rol_requerido("admin", "encargado")
def nuevo():
    form = CategoriaForm()
    if form.validate_on_submit():
        try:
            categoria_service.crear(nombre=form.nombre.data, descripcion=form.descripcion.data)
            flash("Categoría registrada correctamente.", "success")
            return redirect(url_for("categorias.index"))
        except ErrorNegocioCategoria as e:
            flash(str(e), "danger")
    return render_template("categorias/form.html", form=form, titulo="Registrar categoría")


@bp.route("/<int:categoria_id>/editar", methods=["GET", "POST"])
@login_required
@rol_requerido("admin", "encargado")
def editar(categoria_id):
    categoria = categoria_service.obtener(categoria_id)
    if categoria is None:
        abort(404)

    form = CategoriaForm(obj=categoria)
    if form.validate_on_submit():
        try:
            categoria_service.actualizar(categoria, form.nombre.data, form.descripcion.data)
            flash("Categoría actualizada correctamente.", "success")
            return redirect(url_for("categorias.index"))
        except ErrorNegocioCategoria as e:
            flash(str(e), "danger")

    return render_template(
        "categorias/form.html", form=form, titulo="Editar categoría", categoria=categoria
    )


@bp.post("/<int:categoria_id>/estado")
@login_required
@rol_requerido("admin")
def cambiar_estado(categoria_id):
    categoria = categoria_service.obtener(categoria_id)
    if categoria is None:
        abort(404)
    categoria_service.alternar_estado(categoria)
    estado = "activada" if categoria.activo else "desactivada"
    flash(f"Categoría {estado}.", "success")
    return redirect(url_for("categorias.index"))
