"""Pruebas de control de acceso y permisos por rol."""
from tests.conftest import login


def test_panel_requiere_autenticacion(client):
    """El panel exige sesión iniciada."""
    resp = client.get("/", follow_redirects=True)
    assert resp.request.path == "/login"


def test_alimentos_requiere_autenticacion(client):
    """El listado de alimentos exige sesión iniciada."""
    resp = client.get("/alimentos/", follow_redirects=True)
    assert resp.request.path == "/login"


def test_login_page_publica(client):
    """La página de login es pública."""
    resp = client.get("/login")
    assert resp.status_code == 200


def test_crear_alimento_requiere_sesion(client):
    """No se puede crear un alimento sin autenticarse."""
    resp = client.post("/alimentos/nuevo", data={}, follow_redirects=True)
    assert resp.request.path == "/login"


def test_editar_alimento_requiere_admin_o_encargado(client, admin, encargado, app):
    """Un usuario con rol consulta no puede editar alimentos."""
    from app.extensions import db
    from app.models import RolUsuario, Usuario
    from app.models.alimento import Alimento

    with app.app_context():
        db.session.add(
            Alimento(codigo="GASEOS1", nombre="Gaseosa", categoria="bebidas",
                     unidad_medida="unidad", stock_actual=20, stock_minimo=5)
        )
        db.session.commit()
        a_id = db.session.execute(
            db.select(Alimento).where(Alimento.codigo == "GASEOS1")
        ).scalar_one().id

        # Crear usuario de solo consulta
        consulta = Usuario(
            nombre="Solo Consulta", usuario="consulta",
            rol=RolUsuario.CONSULTA, activo=True,
        )
        consulta.set_password("consulta1")
        db.session.add(consulta)
        db.session.commit()

    # Autenticar usuario consulta
    login(client, "consulta", "consulta1")
    resp = client.get(f"/alimentos/{a_id}/editar")
    assert resp.status_code == 403


def test_alternar_estado_solo_admin(client, encargado, app):
    """Solo el administrador puede activar/desactivar alimentos."""
    from app.extensions import db
    from app.models.alimento import Alimento

    with app.app_context():
        db.session.add(
            Alimento(codigo="PAN001", nombre="Pan", categoria="granos",
                     unidad_medida="unidad", stock_actual=30, stock_minimo=10)
        )
        db.session.commit()
        a_id = db.session.execute(
            db.select(Alimento).where(Alimento.codigo == "PAN001")
        ).scalar_one().id

    # Encargado intenta cambiar estado -> 403
    login(client, "encargado", "enc123456")
    resp = client.post(f"/alimentos/{a_id}/estado")
    assert resp.status_code == 403


def test_usuarios_solo_admin(client, encargado):
    """Un encargado no puede acceder a la administración de usuarios."""
    login(client, "encargado", "enc123456")
    resp = client.get("/usuarios/")
    assert resp.status_code == 403
