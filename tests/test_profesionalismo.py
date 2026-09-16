"""Pruebas de pulido profesional (Sprint 8): SEO, seguridad, errores y backups."""
from tests.conftest import login


def test_robots_txt(client):
    resp = client.get("/robots.txt")
    assert resp.status_code == 200
    texto = resp.get_data(as_text=True)
    assert "User-agent: *" in texto
    assert "Sitemap:" in texto


def test_sitemap_xml(client):
    resp = client.get("/sitemap.xml")
    assert resp.status_code == 200
    xml = resp.get_data(as_text=True)
    assert "<urlset" in xml
    assert "xmlns" in xml


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["estado"] == "ok"


def test_cabeceras_seguridad(client):
    resp = client.get("/login")
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-Frame-Options") == "SAMEORIGIN"
    assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


def test_pagina_404(client):
    resp = client.get("/ruta-inexistente")
    assert resp.status_code == 404
    assert "Página no encontrada" in resp.get_data(as_text=True)
    assert "Volver atrás" in resp.get_data(as_text=True)


def test_pagina_404_requiere_login(client):
    """La 404 no debe exigir login para verse."""
    resp = client.get("/ruta-que-no-existe", follow_redirects=True)
    assert resp.status_code == 404


def test_favicon_disponible(client):
    resp = client.get("/static/favicon.svg")
    assert resp.status_code == 200
    assert "image/svg" in resp.headers.get("Content-Type", "")


def test_bloqueo_login_por_intentos(client, app):
    """Tras varios intentos fallidos se bloquea temporalmente el acceso."""
    for i in range(5):
        resp = client.post(
            "/login",
            data={"usuario": "equivocado", "password": "clave_mala"},
            follow_redirects=True,
        )
    # El sexto intento muestra el aviso de bloqueo
    resp = client.post(
        "/login",
        data={"usuario": "admin", "password": "admin123"},
        follow_redirects=True,
    )
    html = resp.get_data(as_text=True)
    assert "Demasiados intentos fallidos" in html


def test_contacto_admin_tras_password_correcta(client, admin):
    """Un login correcto limpia el contador de intentos."""
    for i in range(2):
        client.post(
            "/login",
            data={"usuario": "admin", "password": "mala_clave"},
            follow_redirects=True,
        )
    resp = client.post(
        "/login",
        data={"usuario": "admin", "password": "admin123"},
        follow_redirects=True,
    )
    assert "¡Bienvenido" in resp.get_data(as_text=True)


def test_backup_cli(runner, monkeypatch):
    """El comando backup crea un archivo de respaldo legible."""
    import tempfile, os
    from app.services import backup_service

    # Crear un archivo temporal que simula la BD real del proyecto
    tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    tmp.write(b"fake-db-content")
    tmp.close()

    monkeypatch.setattr(backup_service, "_ruta_bd_actual", lambda: tmp.name)

    resultado = runner.invoke(args=["backup"])
    assert resultado.exit_code == 0, resultado.output
    assert "[OK] Copia de seguridad creada" in resultado.output
    assert backup_service.listar_backups(), "debe existir al menos un respaldo"

    os.unlink(tmp.name)


def test_inicializar_bd_reintenta_colision_concurrencia(app, monkeypatch):
    """En serverless varios procesos siembran en paralelo: ante un
    IntegrityError (clave única ya insertada por otro proceso) la
    inicialización hace rollback e intenta de nuevo sin fallar."""
    from sqlalchemy.exc import IntegrityError

    from app import inicializar_bd
    from app.extensions import db
    from app.models import Alimento, Usuario
    from app.services import simulacion_service

    llamadas = {"n": 0}
    real_generar = simulacion_service.generar_datos_demo

    def generar_con_colision_una_vez(forzar=False):
        llamadas["n"] += 1
        if llamadas["n"] == 1:
            # Simula otro cold start que ya insertó el usuario demo
            db.session.flush()
            from app.models import RolUsuario

            usr = Usuario(
                nombre="Usuario de Demostración",
                usuario="demo",
                rol=RolUsuario.ENCARGADO,
                activo=True,
            )
            usr.set_password("demo123")
            db.session.add(usr)
            db.session.commit()
            simulacion_service.logger.info("Otro proceso sembró el usuario demo")
            raise IntegrityError("colision-demo", {}, ConnectionError("duplicado"))
        return real_generar(forzar=forzar)

    monkeypatch.setattr(simulacion_service, "generar_datos_demo", generar_con_colision_una_vez)

    with app.app_context():
        # Forzamos que el patrón de arranque detecte "BD vacía" y la cree
        db.drop_all()
        inicializar_bd(app)

        # Se recuperó solo: hay alimentos y un único usuario demo
        assert Alimento.query.count() > 0
        assert Usuario.query.filter_by(usuario="demo").count() == 1
        assert llamadas["n"] == 2