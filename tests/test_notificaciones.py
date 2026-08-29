"""Pruebas del Sprint 6: notificaciones, tema y extras profesionales.

Cubre el servicio y las rutas del centro de notificaciones (campana del
topbar), la configuración del tema (marcadores en plantillas) y los extras
profesionales (búsqueda funcional y menú de usuario).
"""
from datetime import date, timedelta

from app.extensions import db
from app.models import Alimento, Lote, Usuario
from app.services import notificaciones_service


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


def _usuario():
    u = Usuario(nombre="Admin", usuario="adminnot", rol="admin", activo=True)
    u.set_password("admin123")
    db.session.add(u)
    db.session.commit()
    return u


# ------------------------------------------------------------ Servicio
def test_notificaciones_sin_alertas(app, categoria_id):
    with app.app_context():
        crear_alimento(app, categoria_id, codigo="NA1", stock_actual=10, stock_minimo=2)
        u = _usuario()
        datos = notificaciones_service.notificaciones_usuario(u)
        assert datos["total"] == 0
        assert datos["no_leidas"] == 0


def test_notificaciones_generadas_y_no_leidas(app, categoria_id):
    with app.app_context():
        a = crear_alimento(app, categoria_id, codigo="NG1", stock_actual=1, stock_minimo=5)
        crear_lote(app, a, "L-NG", dias=2)
        u = _usuario()
        datos = notificaciones_service.notificaciones_usuario(u)
        # stock bajo (1 < 5) y lote a 2 días => al menos 2 notificaciones
        assert datos["total"] >= 2
        assert datos["no_leidas"] == datos["total"]
        tipos = [n["tipo"] for n in datos["items"]]
        assert "stock" in tipos
        assert "vencimiento" in tipos


def test_marcar_leidas_reduce_no_leidas(app, categoria_id):
    with app.app_context():
        a = crear_alimento(app, categoria_id, codigo="ML1", stock_actual=0, stock_minimo=5)
        u = _usuario()
        antes = notificaciones_service.notificaciones_usuario(u)
        marcadas = notificaciones_service.marcar_todas_como_leidas(u)
        assert marcadas >= 1
        despues = notificaciones_service.notificaciones_usuario(u)
        assert despues["no_leidas"] == 0
        assert all(n["leida"] for n in despues["items"])


def test_notificacion_vencimiento_contiene_datos(app, categoria_id):
    with app.app_context():
        a = crear_alimento(app, categoria_id, codigo="NV1", stock_actual=5)
        crear_lote(app, a, "L-NV", dias=1)
        u = _usuario()
        datos = notificaciones_service.notificaciones_usuario(u)
        venc = next(n for n in datos["items"] if n["tipo"] == "vencimiento")
        assert "vence en" in venc["mensaje"]
        assert "L-NV" in venc["mensaje"]
        assert venc["url"] == "/alertas/vence-pronto"
        assert venc["nivel"] == "critica"


# ------------------------------------------------------------ Rutas
def test_ruta_json_notificaciones(cliente_autenticado, app, categoria_id):
    with app.app_context():
        a = crear_alimento(app, categoria_id, codigo="RJ1", stock_actual=1, stock_minimo=6)
    resp = cliente_autenticado.get("/notificaciones/")
    assert resp.status_code == 200
    assert resp.mimetype == "application/json"
    body = resp.get_json()
    assert "items" in body
    assert "no_leidas" in body
    assert body["no_leidas"] >= 1


def test_ruta_marcar_todas_leidas(cliente_autenticado, app, categoria_id):
    with app.app_context():
        crear_alimento(app, categoria_id, codigo="RJ2", stock_actual=0, stock_minimo=4)
    resp = cliente_autenticado.post("/notificaciones/leidas")
    assert resp.status_code == 200
    assert resp.get_json()["ok"] is True
    # ahora no quedan no-leídas
    resp2 = cliente_autenticado.get("/notificaciones/")
    assert resp2.get_json()["no_leidas"] == 0


def test_notificaciones_requiere_sesion(client):
    resp = client.get("/notificaciones/")
    assert resp.status_code == 302  # redirige a login


# ------------------------------------------------------------ Extras
def test_topbar_incluye_botones_profesionales(cliente_autenticado):
    resp = cliente_autenticado.get("/")
    html = resp.get_data(as_text=True)
    assert "themeToggle" in html          # botón de tema
    assert "notifToggle" in html          # campana de notificaciones
    assert "userToggle" in html           # menú de usuario
    assert 'name="q"' in html             # búsqueda funcional
    assert "sidebarBackdrop" in html      # fondo móvil


def test_meta_csrf_presente(cliente_autenticado):
    resp = cliente_autenticado.get("/")
    assert 'name="csrf-token"' in resp.get_data(as_text=True)


def test_sidebar_colapsable_presente(cliente_autenticado):
    resp = cliente_autenticado.get("/")
    html = resp.get_data(as_text=True)
    assert "sidebarCollapse" in html        # botón de colapso
    assert "sidebar-brand" in html
    assert "brand-mark" in html
    assert "nav-text" in html               # etiquetas envueltas para ocultarse al colapsar


def test_css_incluye_colapso(client):
    resp = client.get("/static/css/app.css")
    css = resp.get_data(as_text=True)
    assert "sidebar-collapsed" in css
    assert "--sidebar-w-collapsed" in css or "--sidebar-w" in css