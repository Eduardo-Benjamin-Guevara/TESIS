"""Pruebas de gestión de inventario (Sprint 2): entradas, salidas, stock, disponibilidad e historial."""
from datetime import date

from app.extensions import db
from app.models import Alimento, Lote, Movimiento, TipoMovimiento, Usuario
from app.services import inventario_service
from tests.conftest import login


def crear_alimento(app, categoria_id, codigo="ARROZ001", nombre="Arroz", stock_actual=10):
    a = Alimento(codigo=codigo, nombre=nombre, categoria_id=categoria_id,
                 unidad_medida="kg", stock_actual=stock_actual, stock_minimo=2)
    db.session.add(a)
    db.session.commit()
    return a


def crear_admin():
    admin = Usuario(nombre="Admin", usuario="admininv", rol="admin", activo=True)
    admin.set_password("admin123")
    db.session.add(admin)
    db.session.commit()
    return admin


# ------------------------------------------------------------ Servicio
def test_registrar_entrada_aumenta_stock(app, categoria_id):
    with app.app_context():
        a = crear_alimento(app, categoria_id)
        admin = crear_admin()
        inventario_service.registrar_entrada(a.id, 15, admin, motivo="Compra")
        db.session.refresh(a)
        assert float(a.stock_actual) == 25
        mv = Movimiento.query.filter_by(alimento_id=a.id).first()
        assert mv.tipo == TipoMovimiento.ENTRADA
        assert float(mv.cantidad) == 15
        assert float(mv.stock_resultante) == 25
        assert mv.usuario_id == admin.id


def test_registrar_salida_disminuye_stock(app, categoria_id):
    with app.app_context():
        a = crear_alimento(app, categoria_id, stock_actual=30)
        admin = crear_admin()
        inventario_service.registrar_salida(a.id, 12, admin, motivo="Desayuno")
        db.session.refresh(a)
        assert float(a.stock_actual) == 18
        mv = Movimiento.query.filter_by(alimento_id=a.id).first()
        assert mv.tipo == TipoMovimiento.SALIDA


def test_salida_sin_stock_suficiente_rechazada(app, categoria_id):
    with app.app_context():
        a = crear_alimento(app, categoria_id, stock_actual=5)
        admin = crear_admin()
        try:
            inventario_service.registrar_salida(a.id, 10, admin)
            assert False, "Debió lanzar ErrorInventario"
        except inventario_service.ErrorInventario:
            pass
        db.session.refresh(a)
        assert float(a.stock_actual) == 5  # sin cambios
        assert Movimiento.query.filter_by(alimento_id=a.id).count() == 0


def test_entrada_con_lote_aumenta_ambos(app, categoria_id):
    with app.app_context():
        a = crear_alimento(app, categoria_id, stock_actual=10)
        lote = Lote(alimento_id=a.id, codigo="L-1",
                    fecha_vencimiento=date(2027, 6, 30), cantidad=10)
        db.session.add(lote)
        db.session.commit()
        admin = crear_admin()
        inventario_service.registrar_entrada(a.id, 5, admin, lote_id=lote.id)
        db.session.refresh(a)
        db.session.refresh(lote)
        assert float(a.stock_actual) == 15
        assert float(lote.cantidad) == 15


def test_disponibilidad(app, categoria_id):
    with app.app_context():
        a = crear_alimento(app, categoria_id, stock_actual=20)
        lote = Lote(alimento_id=a.id, codigo="L-2",
                    fecha_vencimiento=date(2027, 5, 1), cantidad=8)
        db.session.add(lote)
        db.session.commit()
        total, lotes = inventario_service.disponibilidad(a.id)
        assert total == 20
        assert any(l.id == lote.id for l in lotes)


def test_cantidad_no_positiva_rechazada(app, categoria_id):
    with app.app_context():
        a = crear_alimento(app, categoria_id)
        admin = crear_admin()
        try:
            inventario_service.registrar_entrada(a.id, 0, admin)
            assert False
        except inventario_service.ErrorInventario:
            pass


# ------------------------------------------------------------ Rutas
def login_admin(client):
    login(client, "admininv", "admin123")
    return True


def test_pagina_disponibilidad(cliente_autenticado, app, categoria_id):
    with app.app_context():
        a = crear_alimento(app, categoria_id)
    resp = cliente_autenticado.get("/inventario/disponibilidad")
    assert resp.status_code == 200
    assert "ARROZ001" in resp.get_data(as_text=True)


def test_registrar_entrada_por_formulario(cliente_autenticado, app, categoria_id):
    with app.app_context():
        a = crear_alimento(app, categoria_id, stock_actual=5)
        a_id = a.id
    data = {"alimento": str(a_id), "cantidad": "20", "lote": "", "motivo": "Compra mensual"}
    resp = cliente_autenticado.post("/inventario/entradas/nueva", data=data, follow_redirects=True)
    assert "registrada" in resp.get_data(as_text=True).lower()
    with app.app_context():
        assert float(db.session.get(Alimento, a_id).stock_actual) == 25


def test_registrar_salida_por_formulario(cliente_autenticado, app, categoria_id):
    with app.app_context():
        a = crear_alimento(app, categoria_id, stock_actual=40)
        a_id = a.id
    data = {"alimento": str(a_id), "cantidad": "10", "lote": "", "motivo": "Uso diario"}
    resp = cliente_autenticado.post("/inventario/salidas/nueva", data=data, follow_redirects=True)
    assert "salida" in resp.get_data(as_text=True).lower()
    with app.app_context():
        assert float(db.session.get(Alimento, a_id).stock_actual) == 30


def test_salida_stock_insuficiente_muestra_error(cliente_autenticado, app, categoria_id):
    with app.app_context():
        a = crear_alimento(app, categoria_id, stock_actual=4)
        a_id = a.id
    data = {"alimento": str(a_id), "cantidad": "50", "lote": ""}
    resp = cliente_autenticado.post("/inventario/salidas/nueva", data=data, follow_redirects=True)
    assert "insuficiente" in resp.get_data(as_text=True).lower()


def test_historial_muestra_movimientos(cliente_autenticado, app, categoria_id):
    with app.app_context():
        a = crear_alimento(app, categoria_id, stock_actual=10)
        admin = crear_admin()
        inventario_service.registrar_entrada(a.id, 5, admin, motivo="Compra")
    resp = cliente_autenticado.get("/inventario/historial")
    assert resp.status_code == 200
    pagina = resp.get_data(as_text=True)
    assert "ARROZ001" in pagina
    assert "Compra" in pagina


def test_historial_filtro_por_tipo(cliente_autenticado, app, categoria_id):
    with app.app_context():
        a = crear_alimento(app, categoria_id, stock_actual=10)
        admin = crear_admin()
        inventario_service.registrar_salida(a.id, 2, admin, motivo="Uso")
    resp = cliente_autenticado.get("/inventario/historial?tipo=entrada")
    assert resp.status_code == 200
    assert "entrada" in resp.get_data(as_text=True).lower()
