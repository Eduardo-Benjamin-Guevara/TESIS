"""Pruebas de monitoreo y reportes (Sprint 4): KPIs, stock en tiempo real y reportes."""
from datetime import date, timedelta

from app.extensions import db
from app.models import Alimento, Lote, Movimiento
from app.services import inventario_service, reportes_service


def crear_alimento(app, categoria_id, codigo="ARROZ001", nombre="Arroz",
                   stock_actual=10, stock_minimo=2):
    a = Alimento(codigo=codigo, nombre=nombre, categoria_id=categoria_id,
                 unidad_medida="kg", stock_actual=stock_actual, stock_minimo=stock_minimo)
    db.session.add(a)
    db.session.commit()
    return a


def crear_lote(app, alimento, codigo="L-1", dias=30, cantidad=10):
    lote = Lote(alimento_id=alimento.id, codigo=codigo,
                fecha_vencimiento=date.today() + timedelta(days=dias),
                cantidad=cantidad, activo=True)
    db.session.add(lote)
    db.session.commit()
    return lote


# ------------------------------------------------------------ Servicio
def test_kpis_alimentos_y_stock(app, categoria_id):
    with app.app_context():
        crear_alimento(app, categoria_id, codigo="K1", stock_actual=5, stock_minimo=2)
        crear_alimento(app, categoria_id, codigo="K2", stock_actual=1, stock_minimo=5)
        k = reportes_service.kpis()
        assert k["total_alimentos"] == 2
        assert k["stock_total"] == 6
        assert k["stock_bajo"] == 1  # K2 tiene stock < mínimo


def test_kpis_movimientos(app, categoria_id):
    with app.app_context():
        a = crear_alimento(app, categoria_id, stock_actual=10)
        usuario = _admin()
        inventario_service.registrar_entrada(a.id, 5, usuario)
        inventario_service.registrar_salida(a.id, 3, usuario)
        k = reportes_service.kpis()
        assert k["entradas"] == 1
        assert k["salidas"] == 1
        assert k["total_movimientos"] == 2


def _admin():
    from app.models import Usuario
    admin = Usuario(nombre="Admin", usuario="adminmon", rol="admin", activo=True)
    admin.set_password("admin123")
    db.session.add(admin)
    db.session.commit()
    return admin


def test_stock_tiempo_real_incluye_desglose(app, categoria_id):
    with app.app_context():
        a = crear_alimento(app, categoria_id, stock_actual=20)
        crear_lote(app, a, "L-1", dias=10, cantidad=8)
        filas = reportes_service.stock_tiempo_real()
        assert any(f["alimento"].codigo == "ARROZ001" for f in filas)
        f = next(x for x in filas if x["alimento"].codigo == "ARROZ001")
        assert float(f["stock"]) == 20


def test_reporte_vencimientos_incluye_proximos(app, categoria_id):
    with app.app_context():
        a = crear_alimento(app, categoria_id, stock_actual=10)
        crear_lote(app, a, "L-E1", dias=2)
        crear_lote(app, a, "L-LEJOS", dias=60)
        lotes = reportes_service.reporte_vencimientos()
        codigos = [l.codigo for l in lotes]
        assert "L-E1" in codigos
        assert "L-LEJOS" not in codigos


def test_reporte_por_categoria(app, categoria_id):
    with app.app_context():
        crear_alimento(app, categoria_id, codigo="C1", stock_actual=4, stock_minimo=1)
        crear_alimento(app, categoria_id, codigo="C2", stock_actual=0, stock_minimo=5)
        filas = reportes_service.reporte_por_categoria()
        assert len(filas) >= 1
        granos = next(f for f in filas if f["categoria"].nombre == "granos")
        assert granos["cantidad"] == 2
        assert granos["bajo"] == 1


def test_actividad_reciente_limita(app, categoria_id):
    with app.app_context():
        a = crear_alimento(app, categoria_id, stock_actual=10)
        admin = _admin()
        inventario_service.registrar_entrada(a.id, 1, admin)
        inventario_service.registrar_salida(a.id, 1, admin)
        actividad = reportes_service.actividad_reciente(limit=1)
        assert len(actividad) == 1


# ------------------------------------------------------------ Rutas
def test_dashboard_monitoreo(cliente_autenticado, app, categoria_id):
    with app.app_context():
        crear_alimento(app, categoria_id, codigo="D1", stock_actual=3, stock_minimo=1)
        crear_lote(app, crear_alimento(app, categoria_id, codigo="D2", stock_actual=3), "L-D", dias=3)
    resp = cliente_autenticado.get("/monitoreo/")
    assert resp.status_code == 200
    assert "Dashboard" in resp.get_data(as_text=True)


def test_stock_tiempo_real_pagina(cliente_autenticado, app, categoria_id):
    with app.app_context():
        crear_alimento(app, categoria_id, codigo="S1", stock_actual=4, stock_minimo=1)
    resp = cliente_autenticado.get("/monitoreo/stock")
    assert resp.status_code == 200
    assert "S1" in resp.get_data(as_text=True)


def test_reportes_pagina(cliente_autenticado, app, categoria_id):
    with app.app_context():
        a = crear_alimento(app, categoria_id, codigo="R1", stock_actual=10)
        crear_lote(app, a, "L-REP", dias=2)
    resp = cliente_autenticado.get("/monitoreo/reportes")
    assert resp.status_code == 200
    assert "L-REP" in resp.get_data(as_text=True)