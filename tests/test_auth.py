"""Pruebas de autenticación: login y logout."""
from tests.conftest import crear_encargado, login


def test_login_exitoso(client, admin):
    """Un usuario con credenciales válidas inicia sesión correctamente."""
    resp = login(client, "admin", "admin123")
    assert resp.status_code == 200
    # Se redirige al panel
    assert resp.request.path == "/"


def test_login_fallido(client, admin):
    """Contraseña incorrecta: no debe iniciar sesión."""
    resp = login(client, "admin", "clave-incorrecta")
    assert resp.status_code == 200
    assert "Credenciales incorrectas".lower() in resp.get_data(as_text=True).lower()
    # Al no autenticarse, se queda en /login
    assert resp.request.path == "/login"


def test_login_usuario_inexistente(client):
    """Usuario que no existe no debe autenticarse."""
    resp = login(client, "noexiste", "cualquiera")
    assert resp.status_code == 200
    assert "Credenciales incorrectas".lower() in resp.get_data(as_text=True).lower()


def test_login_cuenta_inactiva(client, app):
    """Un usuario desactivado no puede iniciar sesión."""
    from app.extensions import db
    from app.models import Usuario

    with app.app_context():
        enc = crear_encargado()
        enc.activo = False
        db.session.commit()
    resp = login(client, "encargado", "enc123456")
    assert "Credenciales incorrectas".lower() in resp.get_data(as_text=True).lower()


def test_logout(client, admin):
    """Cerrar sesión redirige al login."""
    login(client, "admin", "admin123")
    resp = client.get("/logout", follow_redirects=True)
    assert resp.status_code == 200
    assert resp.request.path == "/login"


def test_redireccion_no_autenticado(client):
    """Un usuario sin sesión es redirigido al login al acceder al panel."""
    resp = client.get("/", follow_redirects=True)
    assert resp.request.path == "/login"
