"""Pruebas del asistente inteligente (IA): clasificación de intenciones,
respuestas con datos reales, endpoint JSON y conector externo opcional."""
from app.extensions import db
from app.models import Alimento, Lote, Usuario
from app.services import ia_service
from app.services.ia_service import clasificar, preguntar


def crear_alimento(app, categoria_id, codigo="ARROZ001", nombre="Arroz extra",
                   stock_actual=10, stock_minimo=2):
    a = Alimento(codigo=codigo, nombre=nombre, categoria_id=categoria_id,
                 unidad_medida="kg", stock_actual=stock_actual,
                 stock_minimo=stock_minimo)
    db.session.add(a)
    db.session.commit()
    return a


def _admin():
    admin = Usuario(nombre="Admin", usuario="adminia", rol="admin", activo=True)
    admin.set_password("admin123")
    db.session.add(admin)
    db.session.commit()
    return admin


# ------------------------------------------------------------ Clasificador
def test_clasificador_entrena_todas_las_intenciones():
    modelo = ia_service.entrenar()
    assert set(modelo) == set(ia_service.CORPUS)
    assert all(modelo[i] for i in modelo)  # ninguna lista vacía


def test_clasificar_stock_bajo():
    intencion, confianza = clasificar("¿qué alimentos tienen stock bajo?")
    assert intencion == "stock_bajo"
    assert confianza > 0.4


def test_clasificar_vencimiento():
    intencion, _ = clasificar("¿qué lotes están por vencer pronto?")
    assert intencion == "vencimiento"


def test_clasificar_saludo():
    intencion, _ = clasificar("hola, buenos días")
    assert intencion == "saludo"


def test_clasificar_recomendaciones():
    intencion, _ = clasificar("¿qué me recomiendas comprar?")
    assert intencion == "recomendaciones"


# ------------------------------------------------------------ Respuestas reales
def test_preguntar_resumen_usa_datos(app, categoria_id):
    with app.app_context():
        crear_alimento(app, categoria_id, codigo="IA1", stock_actual=5, stock_minimo=4)
        r = preguntar("dame un resumen del inventario")
        assert r["origen"] == "entrenada"
        assert "Stock total" in r["respuesta"]
        assert "IA1" in r["respuesta"] or "1" in r["respuesta"]


def test_preguntar_stock_bajo_detecta_faltante(app, categoria_id):
    with app.app_context():
        crear_alimento(app, categoria_id, codigo="IA2", nombre="Leche", stock_actual=1, stock_minimo=8)
        r = preguntar("¿qué alimentos tienen stock bajo?")
        assert r["intencion"] == "stock_bajo"
        assert "Leche" in r["respuesta"]


def test_preguntar_alimento_especifico(app, categoria_id):
    with app.app_context():
        crear_alimento(app, categoria_id, codigo="AVENA1", nombre="Avena", stock_actual=6, stock_minimo=2)
        r = preguntar("¿cuánto stock hay de avena?")
        assert r["intencion"] == "alimento"
        assert "Avena" in r["respuesta"]
        assert "AVENA1" in r["respuesta"]


def test_preguntar_vencimientos(app, categoria_id):
    from datetime import date, timedelta

    with app.app_context():
        a = crear_alimento(app, categoria_id, codigo="IA3")
        lote = Lote(alimento_id=a.id, codigo="L-IA3",
                    fecha_vencimiento=date.today() + timedelta(days=2),
                    cantidad=3, activo=True)
        db.session.add(lote)
        db.session.commit()
        r = preguntar("¿qué alimentos vencen pronto?")
        assert r["intencion"] == "vencimiento"
        assert "ARROZ001" in r["respuesta"] or "IA3" in r["respuesta"]


def test_preguntar_sin_mensaje_devuelve_ayuda(app):
    with app.app_context():
        r = preguntar("   ")
        assert r["intencion"] == "ayuda"
        assert r["respuesta"]


def test_preguntar_desconocida_devuelve_fallback(app):
    with app.app_context():
        r = preguntar("xyzzy qwerty zzz")
        assert r["intencion"] == "no_identificada"


# ------------------------------------------------------------ Endpoint HTTP
def test_pagina_chat_requiere_login(client, app):
    resp = client.get("/ia/")
    assert resp.status_code < 400  # redirige a login (302), no error 500


def test_pagina_chat_autenticada(cliente_autenticado, app, categoria_id):
    with app.app_context():
        crear_alimento(app, categoria_id, codigo="IA4")
    resp = cliente_autenticado.get("/ia/")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "Asistente inteligente" in html
    assert 'id="iaMensajes"' in html
    assert "js/ia.js" in html


def test_api_preguntar_devuelve_json(cliente_autenticado, app, categoria_id):
    with app.app_context():
        crear_alimento(app, categoria_id, codigo="IA5")
    resp = cliente_autenticado.post(
        "/ia/api/preguntar", json={"mensaje": "¿qué alimentos tienen stock bajo?"}
    )
    assert resp.status_code == 200
    datos = resp.get_json()
    assert datos["origen"] == "entrenada"
    assert datos["intencion"] == "stock_bajo"
    assert datos["respuesta"]
    assert datos["error"] == ""


def test_api_preguntar_sin_mensaje_400(cliente_autenticado):
    resp = cliente_autenticado.post("/ia/api/preguntar", json={"mensaje": ""})
    assert resp.status_code == 400
    assert resp.get_json()["error"]


# ------------------------------------------------------------ IA externa
def test_ia_externa_sin_clave_levanta_error(app):
    with app.app_context():
        app.config["IA_API_KEY"] = ""
        try:
            ia_service.consultar_ia_externa("hola")
            assert False, "debió fallar sin clave configurada"
        except ia_service.ErrorIA:
            pass


def test_preguntar_sin_clave_usa_modelo_integrado(app, categoria_id):
    with app.app_context():
        app.config["IA_API_KEY"] = ""
        crear_alimento(app, categoria_id, codigo="IA6")
        r = preguntar("¿qué alimentos tienen stock bajo?")
        assert r["origen"] == "entrenada"