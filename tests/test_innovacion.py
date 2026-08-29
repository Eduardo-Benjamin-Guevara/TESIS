"""Pruebas de funcionalidades innovadoras (Sprint 5): QR, trazabilidad,
recomendaciones de compra, exportación y gráficos del dashboard."""
from datetime import date, timedelta

from openpyxl import load_workbook

from app.extensions import db
from app.models import Alimento, Lote, Usuario
from app.services import (
    exportacion_service,
    inventario_service,
    qr_service,
    recomendaciones_service,
    trazabilidad_service,
)


def crear_alimento(app, categoria_id, codigo="ARROZ001", nombre="Arroz",
                   stock_actual=10, stock_minimo=2):
    a = Alimento(codigo=codigo, nombre=nombre, categoria_id=categoria_id,
                 unidad_medida="kg", stock_actual=stock_actual, stock_minimo=stock_minimo)
    db.session.add(a)
    db.session.commit()
    return a


def _admin():
    admin = Usuario(nombre="Admin", usuario="adminqr", rol="admin", activo=True)
    admin.set_password("admin123")
    db.session.add(admin)
    db.session.commit()
    return admin


# ------------------------------------------------------------ Servicio QR
def test_generar_qr_devuelve_png(app, categoria_id):
    with app.app_context():
        a = crear_alimento(app, categoria_id, codigo="QR1")
        png = qr_service.generar_qr(a)
        assert png[:8] == b"\x89PNG\r\n\x1a\n"  # cabecera PNG
        assert len(png) > 100


def test_generar_qr_incluye_datos_extra(app, categoria_id):
    with app.app_context():
        a = crear_alimento(app, categoria_id, codigo="QR2")
        png = qr_service.generar_qr(a, {"lote": "L-QR"})
        assert png[:8] == b"\x89PNG\r\n\x1a\n"


# ------------------------------------------------------------ Trazabilidad
def test_trazabilidad_reconstruye_movimientos(app, categoria_id):
    with app.app_context():
        a = crear_alimento(app, categoria_id, stock_actual=0)
        admin = _admin()
        inventario_service.registrar_entrada(a.id, 10, admin)
        inventario_service.registrar_salida(a.id, 3, admin)
        datos = trazabilidad_service.trazabilidad_alimento(a.id)
        assert datos["alimento"].codigo == "ARROZ001"
        assert len(datos["movimientos"]) == 2
        assert datos["total_entradas"] == 10
        assert datos["total_salidas"] == 3


# ------------------------------------------------------------ Recomendaciones
def test_recomendacion_por_stock_bajo(app, categoria_id):
    with app.app_context():
        crear_alimento(app, categoria_id, codigo="REC1", stock_actual=1, stock_minimo=5)
        items = recomendaciones_service.recomendaciones()
        assert len(items) == 1
        r = items[0]
        assert r["faltante"] == 4
        assert r["cantidad_sugerida"] == 9  # objetivo (10) - actual (1)
        assert r["urgente"] is False


def test_recomendacion_urgente_sin_stock(app, categoria_id):
    with app.app_context():
        crear_alimento(app, categoria_id, codigo="REC2", stock_actual=0, stock_minimo=4)
        items = recomendaciones_service.recomendaciones()
        assert items[0]["urgente"] is True


def test_sin_recomendacion_con_stock_suficiente(app, categoria_id):
    with app.app_context():
        crear_alimento(app, categoria_id, codigo="REC3", stock_actual=10, stock_minimo=2)
        assert recomendaciones_service.recomendaciones() == []


# ------------------------------------------------------------ Exportación
def test_exportar_csv_con_bom_y_cabecera(app, categoria_id):
    with app.app_context():
        filas = [{"codigo": "X1", "alimento": "Arroz", "cantidad": 3.0}]
        contenido = exportacion_service.exportar_csv(filas)
        texto = contenido.decode("utf-8")
        assert texto.startswith("\ufeff")  # BOM para Excel
        assert "codigo,alimento,cantidad" in texto
        assert "X1,Arroz" in texto


def test_exportar_excel_incluye_datos(app, categoria_id):
    with app.app_context():
        filas = [{"codigo": "X1", "alimento": "Arroz", "cantidad": 3.0}]
        contenido = exportacion_service.exportar_excel("Inventario", filas)
        libro = load_workbook(io_bytes(contenido))
        hoja = libro.active
        assert hoja.title == "Inventario"
        assert hoja["A1"].value == "codigo"
        assert hoja["A2"].value == "X1"


def io_bytes(data: bytes):
    import io

    return io.BytesIO(data)


# ------------------------------------------------------------ Rutas
def test_ruta_qr_devuelve_imagen(cliente_autenticado, app, categoria_id):
    with app.app_context():
        a = crear_alimento(app, categoria_id, codigo="QR3")
        id_alimento = a.id
    resp = cliente_autenticado.get(f"/alimentos/{id_alimento}/qr")
    assert resp.status_code == 200
    assert resp.mimetype == "image/png"
    assert resp.data[:8] == b"\x89PNG\r\n\x1a\n"


def test_ruta_trazabilidad(cliente_autenticado, app, categoria_id):
    with app.app_context():
        a = crear_alimento(app, categoria_id, codigo="TZ1")
        admin = _admin()
        inventario_service.registrar_entrada(a.id, 5, admin)
        id_alimento = a.id
    resp = cliente_autenticado.get(f"/alimentos/{id_alimento}/trazabilidad")
    assert resp.status_code == 200
    assert "Trazabilidad" in resp.get_data(as_text=True)
    assert "Entrada" in resp.get_data(as_text=True)


def test_ruta_recomendaciones(cliente_autenticado, app, categoria_id):
    with app.app_context():
        crear_alimento(app, categoria_id, codigo="REC4", stock_actual=1, stock_minimo=6)
    resp = cliente_autenticado.get("/monitoreo/recomendaciones")
    assert resp.status_code == 200
    assert "REC4" in resp.get_data(as_text=True)


def test_ruta_exportar_csv(cliente_autenticado, app, categoria_id):
    with app.app_context():
        a = crear_alimento(app, categoria_id, codigo="EXP1", stock_actual=3)
        lote = Lote(alimento_id=a.id, codigo="L-EXP",
                    fecha_vencimiento=date.today() + timedelta(days=2),
                    cantidad=3, activo=True)
        db.session.add(lote)
        db.session.commit()
    resp = cliente_autenticado.get("/monitoreo/reportes/exportar?formato=csv")
    assert resp.status_code == 200
    assert resp.mimetype.startswith("text/csv")
    assert b"EXP1" in resp.data


def test_ruta_exportar_excel(cliente_autenticado, app, categoria_id):
    with app.app_context():
        a = crear_alimento(app, categoria_id, codigo="EXP2", stock_actual=3)
        lote = Lote(alimento_id=a.id, codigo="L-EXP2",
                    fecha_vencimiento=date.today() + timedelta(days=2),
                    cantidad=3, activo=True)
        db.session.add(lote)
        db.session.commit()
    resp = cliente_autenticado.get("/monitoreo/reportes/exportar?formato=xlsx")
    assert resp.status_code == 200
    assert (
        resp.mimetype
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert resp.data[:2] == b"PK"  # firma ZIP/ xlsx


def test_dashboard_incluye_graficos(cliente_autenticado, app, categoria_id):
    with app.app_context():
        crear_alimento(app, categoria_id, codigo="GR1", stock_actual=5)
    resp = cliente_autenticado.get("/monitoreo/")
    html = resp.get_data(as_text=True)
    assert resp.status_code == 200
    assert 'id="chartCategorias"' in html
    assert 'id="chartEstado"' in html
    assert "chart.js" in html


def test_detalle_incluye_qr_y_trazabilidad(cliente_autenticado, app, categoria_id):
    with app.app_context():
        a = crear_alimento(app, categoria_id, codigo="DT1")
        id_alimento = a.id
    resp = cliente_autenticado.get(f"/alimentos/{id_alimento}")
    html = resp.get_data(as_text=True)
    assert "qr-code" in html
    assert "Trazabilidad" in html