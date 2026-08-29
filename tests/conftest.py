"""Fixture compartidos para las pruebas automatizadas."""
import pytest

from app import create_app
from app.extensions import db
from app.models import RolUsuario, Usuario


@pytest.fixture()
def app():
    """Crea una aplicación de pruebas con una base de datos en memoria."""
    app = create_app("testing")
    app.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
    )
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    """Cliente HTTP de pruebas."""
    return app.test_client()


@pytest.fixture()
def runner(app):
    """Runner de comandos Flask para pruebas."""
    return app.test_cli_runner()


def crear_admin():
    """Crea un usuario administrador de prueba."""
    admin = Usuario(
        nombre="Admin Prueba",
        usuario="admin",
        rol=RolUsuario.ADMIN,
        activo=True,
    )
    admin.set_password("admin123")
    db.session.add(admin)
    db.session.commit()
    return admin


def crear_encargado():
    """Crea un usuario encargado de prueba."""
    encargado = Usuario(
        nombre="Encargado Prueba",
        usuario="encargado",
        rol=RolUsuario.ENCARGADO,
        activo=True,
    )
    encargado.set_password("enc123456")
    db.session.add(encargado)
    db.session.commit()
    return encargado


@pytest.fixture()
def admin(app):
    with app.app_context():
        return crear_admin()


@pytest.fixture()
def encargado(app):
    with app.app_context():
        return crear_encargado()


def login(client, usuario="admin", password="admin123"):
    """Autentica al cliente de pruebas y devuelve el usuario."""
    return client.post(
        "/login",
        data={"usuario": usuario, "password": password},
        follow_redirects=True,
    )


@pytest.fixture()
def cliente_autenticado(client, admin):
    """Cliente con sesión de administrador iniciada."""
    login(client, "admin", "admin123")
    return client


# Datos básicos para crear un alimento
DATOS_ALIMENTO = {
    "codigo": "ARROZ001",
    "nombre": "Arroz extra",
    "categoria": "granos",
    "unidad_medida": "kg",
    "stock_actual": "10",
    "stock_minimo": "3",
    "descripcion": "Arroz de primera calidad",
}
