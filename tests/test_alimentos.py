"""Pruebas del CRUD de alimentos y reglas de negocio."""
from tests.conftest import DATOS_ALIMENTO, login


def test_listar_alimentos(cliente_autenticado):
    """La página de alimentos se carga y muestra los registros."""
    resp = cliente_autenticado.get("/alimentos/")
    assert resp.status_code == 200
    assert "Alimentos".lower() in resp.get_data(as_text=True).lower()


def test_registrar_alimento(cliente_autenticado):
    """Registrar un alimento con datos válidos lo crea."""
    resp = cliente_autenticado.post("/alimentos/nuevo", data=DATOS_ALIMENTO, follow_redirects=True)
    assert resp.status_code == 200
    assert "registrado correctamente".lower() in resp.get_data(as_text=True).lower()
    # El código se muestra en el listado (en mayúsculas)
    assert "ARROZ001" in resp.get_data(as_text=True)


def test_registrar_alimento_campos_obligatorios(cliente_autenticado):
    """Faltar campos obligatorios muestra errores de validación."""
    datos_invalidos = DATOS_ALIMENTO.copy()
    datos_invalidos.pop("nombre")
    resp = cliente_autenticado.post("/alimentos/nuevo", data=datos_invalidos)
    assert resp.status_code == 200
    assert "nombre" in resp.get_data(as_text=True).lower()


def test_editar_alimento(cliente_autenticado, app):
    """Editar un alimento actualiza sus datos."""
    from app.extensions import db
    from app.models.alimento import Alimento

    # Crear un alimento directamente
    with app.app_context():
        a = Alimento(
            codigo="LECHE01", nombre="Leche", categoria="lacteos",
            unidad_medida="litro", stock_actual=5, stock_minimo=1,
        )
        db.session.add(a)
        db.session.commit()
        a_id = a.id

    datos_editados = {
        "codigo": "LECHE01",
        "nombre": "Leche fresca",
        "categoria": "lacteos",
        "unidad_medida": "litro",
        "stock_actual": "12",
        "stock_minimo": "2",
        "descripcion": "",
    }
    resp = cliente_autenticado.post(
        f"/alimentos/{a_id}/editar", data=datos_editados, follow_redirects=True
    )
    assert resp.status_code == 200
    assert "actualizado correctamente".lower() in resp.get_data(as_text=True).lower()

    with app.app_context():
        actualizado = db.session.get(Alimento, a_id)
        assert actualizado.nombre == "Leche fresca"
        assert float(actualizado.stock_actual) == 12


def test_consultar_alimento(cliente_autenticado, app):
    """Consultar el detalle de un alimento muestra su información."""
    from app.extensions import db
    from app.models.alimento import Alimento

    with app.app_context():
        a = Alimento(
            codigo="AZUCAR1", nombre="Azúcar rubia", categoria="abarrotes",
            unidad_medida="kg", stock_actual=8, stock_minimo=2,
        )
        db.session.add(a)
        db.session.commit()
        a_id = a.id

    resp = cliente_autenticado.get(f"/alimentos/{a_id}")
    assert resp.status_code == 200
    pagina = resp.get_data(as_text=True)
    assert "Azúcar rubia" in pagina
    assert "AZUCAR1" in pagina


def test_busqueda_y_filtro(cliente_autenticado):
    """La búsqueda por código/nombre filtra el listado."""
    resp = cliente_autenticado.get("/alimentos/?q=ARROZ")
    assert resp.status_code == 200
    assert "No se encontraron" in resp.get_data(as_text=True)


def test_codigo_duplicado(cliente_autenticado, app):
    """No se permite registrar dos alimentos con el mismo código."""
    from app.extensions import db
    from app.models.alimento import Alimento

    with app.app_context():
        db.session.add(
            Alimento(codigo="ARROZ001", nombre="Arroz", categoria="granos",
                     unidad_medida="kg", stock_actual=5, stock_minimo=1)
        )
        db.session.commit()

    resp = cliente_autenticado.post("/alimentos/nuevo", data=DATOS_ALIMENTO, follow_redirects=True)
    assert "ya existe un alimento con ese código".lower() in resp.get_data(as_text=True).lower()
