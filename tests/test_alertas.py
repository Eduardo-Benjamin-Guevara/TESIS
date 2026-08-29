"""Pruebas del sistema de alertas (Sprint 3): próximos a vencer, stock bajo y priorización."""
from datetime import date, timedelta

from app.extensions import db
from app.models import Alimento, Lote
from app.services import alertas_service


def crear_alimento(app, categoria_id, codigo="ARROZ001", nombre="Arroz",
                   stock_actual=10, stock_minimo=2):
    a = Alimento(codigo=codigo, nombre=nombre, categoria_id=categoria_id,
                 unidad_medida="kg", stock_actual=stock_actual, stock_minimo=stock_minimo)
    db.session.add(a)
    db.session.commit()
    return a


def crear_lote(app, alimento, codigo="L-1", dias=30, cantidad=10, activo=True):
    lote = Lote(alimento_id=alimento.id, codigo=codigo,
                fecha_vencimiento=date.today() + timedelta(days=dias),
                cantidad=cantidad, activo=activo)
    db.session.add(lote)
    db.session.commit()
    return lote


# ------------------------------------------------------------ Servicio
def test_proximos_a_vencer_clasifica_prioridad(app, categoria_id):
    with app.app_context():
        a1 = crear_alimento(app, categoria_id, codigo="A001", stock_actual=10)
        a2 = crear_alimento(app, categoria_id, codigo="A002", stock_actual=10)
        crear_lote(app, a1, "L-CRIT", dias=2)   # crítica
        crear_lote(app, a2, "L-MED", dias=12)   # media
        resultado = alertas_service.proximos_a_vencer()
        por_codigo = {}
        for r in resultado:
            por_codigo[r["lote"].codigo] = r["nivel"]
        assert por_codigo["L-CRIT"] == "critica"
        assert por_codigo["L-MED"] == "media"


def test_lote_fuera_de_umbral_no_genera_alerta(app, categoria_id):
    with app.app_context():
        a = crear_alimento(app, categoria_id, stock_actual=10)
        crear_lote(app, a, "L-LEJOS", dias=60)
        assert alertas_service.proximos_a_vencer() == []


def test_lote_vencido_es_critico(app, categoria_id):
    with app.app_context():
        a = crear_alimento(app, categoria_id, stock_actual=10)
        crear_lote(app, a, "L-VENC", dias=-5)
        resultado = alertas_service.proximos_a_vencer()
        assert any(r["nivel"] == "critica" and r["dias"] < 0 for r in resultado)


def test_lote_inactivo_no_genera_alerta(app, categoria_id):
    with app.app_context():
        a = crear_alimento(app, categoria_id, stock_actual=10)
        crear_lote(app, a, "L-INAC", dias=2, activo=False)
        assert alertas_service.proximos_a_vencer() == []


def test_stock_bajo_clasifica_prioridad(app, categoria_id):
    with app.app_context():
        a1 = crear_alimento(app, categoria_id, codigo="S001", stock_actual=0, stock_minimo=5)
        a2 = crear_alimento(app, categoria_id, codigo="S002", stock_actual=1, stock_minimo=5)
        a3 = crear_alimento(app, categoria_id, codigo="S003", stock_actual=4, stock_minimo=5)
        resultado = alertas_service.stock_bajo()
        por_codigo = {r["alimento"].codigo: r["nivel"] for r in resultado}
        assert por_codigo["S001"] == "critica"
        assert por_codigo["S002"] == "alta"
        assert por_codigo["S003"] == "media"


def test_stock_con_minimo_no_definido_sin_alerta(app, categoria_id):
    with app.app_context():
        a = crear_alimento(app, categoria_id, codigo="S004", stock_actual=3, stock_minimo=0)
        assert alertas_service.stock_bajo() == []


def test_contar_resumen(app, categoria_id):
    with app.app_context():
        a1 = crear_alimento(app, categoria_id, codigo="C001", stock_actual=0, stock_minimo=5)
        crear_lote(app, a1, "L-1", dias=1)
        resumen = alertas_service.contar()
        assert resumen["total"] >= 2
        assert resumen["critica"] >= 2


# ------------------------------------------------------------ Rutas
def test_pagina_alertas(cliente_autenticado, app, categoria_id):
    with app.app_context():
        a1 = crear_alimento(app, categoria_id, codigo="R001", stock_actual=1, stock_minimo=5)
        crear_lote(app, a1, "L-1", dias=2)
    resp = cliente_autenticado.get("/alertas/")
    assert resp.status_code == 200
    pagina = resp.get_data(as_text=True)
    assert "Sistema de alertas" in pagina
    assert "R001" in pagina


def test_pagina_vence_pronto(cliente_autenticado, app, categoria_id):
    with app.app_context():
        a = crear_alimento(app, categoria_id, codigo="V001", stock_actual=10)
        crear_lote(app, a, "L-1", dias=3)
    resp = cliente_autenticado.get("/alertas/vence-pronto")
    assert resp.status_code == 200
    assert "V001" in resp.get_data(as_text=True)


def test_pagina_stock_bajo(cliente_autenticado, app, categoria_id):
    with app.app_context():
        crear_alimento(app, categoria_id, codigo="B001", stock_actual=1, stock_minimo=5)
    resp = cliente_autenticado.get("/alertas/stock-bajo")
    assert resp.status_code == 200
    assert "B001" in resp.get_data(as_text=True)


def test_badge_alertas_en_panel(cliente_autenticado, app, categoria_id):
    with app.app_context():
        a = crear_alimento(app, categoria_id, codigo="P001", stock_actual=0, stock_minimo=5)
        crear_lote(app, a, "L-1", dias=1)
    resp = cliente_autenticado.get("/")
    assert resp.status_code == 200
