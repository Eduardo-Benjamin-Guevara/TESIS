"""Rutas del CRUD de alimentos."""
from flask import (
    Blueprint,
    Response,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import login_required
from flask_wtf import FlaskForm
from wtforms import DecimalField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, InputRequired, NumberRange, Optional

from app.services import (
    alimento_service,
    categoria_service,
    lote_service,
    qr_service,
    trazabilidad_service,
)
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
    categoria = SelectField("Categoría", validators=[DataRequired()])
    unidad_medida = StringField(
        "Unidad de medida",
        validators=[DataRequired()],
        render_kw={"placeholder": "Ej. kg, g, unidad, litro", "maxlength": "30"},
    )
    stock_actual = DecimalField(
        "Stock actual",
        validators=[InputRequired(), NumberRange(min=0)],
        render_kw={"placeholder": "0.00", "step": "0.01"},
        places=2,
    )
    stock_minimo = DecimalField(
        "Stock mínimo",
        validators=[InputRequired(), NumberRange(min=0)],
        render_kw={"placeholder": "0.00", "step": "0.01"},
        places=2,
    )
    descripcion = TextAreaField(
        "Descripción",
        validators=[Optional()],
        render_kw={"rows": "3", "maxlength": "500"},
    )


def _opciones_categorias():
    """Lista de (id, nombre_capitalizado) de las categorías activas."""
    return [(str(c.id), c.nombre.capitalize()) for c in categoria_service.listar()]


@bp.route("/")
@login_required
def index():
    """Listado y búsqueda de alimentos."""
    filtro = request.args.get("q", "").strip()
    categoria_id = request.args.get("categoria", "").strip()
    incluir_inactivos = request.args.get("inactivos", "").lower() in ("1", "true", "si")

    alimentos = alimento_service.listar(
        filtro=filtro, categoria_id=categoria_id, incluir_inactivos=incluir_inactivos
    )
    return render_template(
        "alimentos/index.html",
        alimentos=alimentos,
        filtro=filtro,
        categoria_id=categoria_id,
        incluir_inactivos=incluir_inactivos,
    )


@bp.route("/nuevo", methods=["GET", "POST"])
@login_required
@rol_requerido("admin", "encargado")
def nuevo():
    form = AlimentoForm()
    form.categoria.choices = [("", "Seleccione...")] + _opciones_categorias()
    if form.validate_on_submit():
        try:
            alimento_service.crear_alimento(
                codigo=form.codigo.data,
                nombre=form.nombre.data,
                categoria_id=form.categoria.data,
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
    form.categoria.choices = [("", "Seleccione...")] + _opciones_categorias()
    # Asegurar el valor preseleccionado
    if form.categoria.data is None and alimento.categoria_id:
        form.categoria.data = str(alimento.categoria_id)

    if form.validate_on_submit():
        try:
            alimento_service.actualizar_alimento(
                alimento,
                codigo=form.codigo.data,
                nombre=form.nombre.data,
                categoria_id=form.categoria.data,
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
    lotes = lote_service.listar_por_alimento(alimento_id)
    return render_template("alimentos/detalle.html", alimento=alimento, lotes=lotes)


@bp.route("/<int:alimento_id>/qr")
@login_required
def qr(alimento_id):
    """Genera el código QR del alimento (imagen PNG)."""
    alimento = alimento_service.obtener(alimento_id)
    if alimento is None:
        abort(404)
    qr_png = qr_service.generar_qr(alimento)
    return Response(
        qr_png,
        mimetype="image/png",
        headers={
            "Content-Disposition": f'inline; filename="qr_{alimento.codigo}.png"'
        },
    )


@bp.route("/<int:alimento_id>/trazabilidad")
@login_required
def trazabilidad(alimento_id):
    """Historial completo del alimento (trazabilidad total)."""
    try:
        datos = trazabilidad_service.trazabilidad_alimento(alimento_id)
    except Exception:
        abort(404)
    return render_template("alimentos/trazabilidad.html", data=datos)


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
