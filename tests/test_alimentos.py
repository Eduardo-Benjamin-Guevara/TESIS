"""Pruebas del CRUD de alimentos, categorías y lotes (Sprint 1)."""
from app.extensions import db
from app.models import Categoria, Lote
from app.models.alimento import Alimento
from tests.conftest import DATOS_ALIMENTO, crear_admin, login

# Datos de alimento listos para enviar por POST (con categoria = id)
def datos_alimento(categoria_id, **extra):
    data = dict(DATOS_ALIMENTO)
    data["categoria"] = str(categoria_id)
    data.update(extra)
    return data


def crear_alimento_db(categoria_id, codigo="LECHE01", nombre="Leche", categoria_nombre=None,
                      unidad_medida="litro", stock_actual=5, stock_minimo=1):
    cat_id = categoria_id
    if categoria_nombre:
        cat = Categoria.query.filter_by(nombre=categoria_nombre).first() or Categoria(nombre=categoria_nombre)
        db.session.add(cat)
        db.session.commit()
        cat_id = cat.id
    a = Alimento(codigo=codigo, nombre=nombre, categoria_id=cat_id,
                 unidad_medida=unidad_medida, stock_actual=stock_actual, stock_minimo=stock_minimo)
    db.session.add(a)
    db.session.commit()
    return a


# ------------------------------------------------------------ Alimentos
def test_listar_alimentos(cliente_autenticado):
    resp = cliente_autenticado.get("/alimentos/")
    assert resp.status_code == 200
    assert "Alimentos".lower() in resp.get_data(as_text=True).lower()


def test_registrar_alimento(cliente_autenticado, categoria_id):
    resp = cliente_autenticado.post("/alimentos/nuevo", data=datos_alimento(categoria_id), follow_redirects=True)
    assert resp.status_code == 200
    assert "registrado correctamente".lower() in resp.get_data(as_text=True).lower()
    assert "ARROZ001" in resp.get_data(as_text=True)


def test_registrar_alimento_campos_obligatorios(cliente_autenticado, categoria_id):
    datos_invalidos = datos_alimento(categoria_id)
    datos_invalidos.pop("nombre")
    resp = cliente_autenticado.post("/alimentos/nuevo", data=datos_invalidos)
    assert resp.status_code == 200
    assert "nombre" in resp.get_data(as_text=True).lower()


def test_editar_alimento(cliente_autenticado, categoria_id, app):
    with app.app_context():
        a = crear_alimento_db(categoria_id)
        a_id = a.id
    datos_editados = datos_alimento(categoria_id, nombre="Leche fresca", stock_actual="12", stock_minimo="2")
    resp = cliente_autenticado.post(f"/alimentos/{a_id}/editar", data=datos_editados, follow_redirects=True)
    assert resp.status_code == 200
    assert "actualizado correctamente".lower() in resp.get_data(as_text=True).lower()
    with app.app_context():
        actualizado = db.session.get(Alimento, a_id)
        assert actualizado.nombre == "Leche fresca"
        assert float(actualizado.stock_actual) == 12


def test_consultar_alimento(cliente_autenticado, categoria_id, app):
    with app.app_context():
        a = crear_alimento_db(categoria_id, codigo="AZUCAR1", nombre="Azúcar rubia", unidad_medida="kg", stock_actual=8, stock_minimo=2)
        a_id = a.id
    resp = cliente_autenticado.get(f"/alimentos/{a_id}")
    assert resp.status_code == 200
    pagina = resp.get_data(as_text=True)
    assert "Azúcar rubia" in pagina
    assert "AZUCAR1" in pagina


def test_codigo_duplicado(cliente_autenticado, categoria_id, app):
    with app.app_context():
        crear_alimento_db(categoria_id, codigo="ARROZ001", nombre="Arroz")
    resp = cliente_autenticado.post("/alimentos/nuevo", data=datos_alimento(categoria_id), follow_redirects=True)
    assert "ya existe un alimento con ese código".lower() in resp.get_data(as_text=True).lower()


# ------------------------------------------------------------ Categorías
def test_registrar_categoria(cliente_autenticado, app):
    resp = cliente_autenticado.post("/categorias/nuevo", data={"nombre": "cereales"}, follow_redirects=True)
    assert "registrada correctamente".lower() in resp.get_data(as_text=True).lower()
    with app.app_context():
        assert Categoria.query.filter_by(nombre="cereales").first() is not None


def test_categoria_duplicada(cliente_autenticado):
    """No se permite registrar una categoría cuyo nombre ya existe."""
    resp = cliente_autenticado.post("/categorias/nuevo", data={"nombre": "granos"}, follow_redirects=True)
    assert "ya existe una categoría".lower() in resp.get_data(as_text=True).lower()


# ------------------------------------------------------------ Lotes
def test_listar_lotes(cliente_autenticado):
    resp = cliente_autenticado.get("/lotes/")
    assert resp.status_code == 200


def test_registrar_lote_y_actualiza_stock(cliente_autenticado, categoria_id, app):
    with app.app_context():
        a = crear_alimento_db(categoria_id, codigo="ARROZ001", nombre="Arroz", stock_actual=10)
        a_id = a.id
    data = {
        "alimento": str(a_id),
        "codigo": "LOTE-A1",
        "fecha_vencimiento": "2027-06-30",
        "fecha_ingreso": "2026-08-01",
        "cantidad": "25",
    }
    resp = cliente_autenticado.post("/lotes/nuevo", data=data, follow_redirects=True)
    assert "lote registrado".lower() in resp.get_data(as_text=True).lower()
    with app.app_context():
        lote = Lote.query.filter_by(codigo="LOTE-A1").first()
        assert lote is not None
        assert lote.alimento_id == a_id
        # El stock del alimento se incrementó en 25
        alimento = db.session.get(Alimento, a_id)
        assert float(alimento.stock_actual) == 35


def test_registrar_lote_cantidad_invalida(cliente_autenticado, categoria_id, app):
    with app.app_context():
        a = crear_alimento_db(categoria_id, codigo="ARROZ002", nombre="Arroz")
        a_id = a.id
    data = {
        "alimento": str(a_id),
        "codigo": "LOTE-B1",
        "fecha_vencimiento": "2027-06-30",
        "cantidad": "0",
    }
    resp = cliente_autenticado.post("/lotes/nuevo", data=data, follow_redirects=True)
    assert "mayor que cero".lower() in resp.get_data(as_text=True).lower()
