"""Pruebas del servicio de datos de simulación (Sprint 7)."""
from datetime import date

import pytest

from app.extensions import db
from app.models import Alimento, Lote, Movimiento, RolUsuario, Usuario
from app.services.simulacion_service import (
    ALIMENTOS_DEMO,
    PASSWORD_DEMO,
    USUARIO_DEMO,
    existen_datos_demo,
    generar_datos_demo,
)


@pytest.fixture()
def sembrados(app):
    """Genera los datos demo una vez para cada prueba."""
    return generar_datos_demo()


def test_genera_alimentos_lotes_y_movimientos(sembrados):
    assert Alimento.query.count() == len(ALIMENTOS_DEMO)
    assert Lote.query.count() > 0
    assert Movimiento.query.count() > 0
    assert sembrados["creado"] is True
    assert sembrados["usuario_demo"] == USUARIO_DEMO


def test_crea_usuario_demo(sembrados):
    demo = Usuario.query.filter_by(usuario=USUARIO_DEMO).first()
    assert demo is not None
    assert demo.rol == RolUsuario.ENCARGADO
    assert demo.check_password(PASSWORD_DEMO)


def test_stock_coherente_con_lotes(sembrados):
    for alimento in Alimento.query.all():
        suma_lotes = sum(float(l.cantidad) for l in alimento.lotes if l.activo)
        assert float(alimento.stock_actual) == suma_lotes


def test_hay_vencimientos_variados(sembrados):
    hoy = date.today()
    vencidos = [l for l in Lote.query.all() if l.fecha_vencimiento <= hoy]
    proximos = [
        l for l in Lote.query.all()
        if hoy < l.fecha_vencimiento and (l.fecha_vencimiento - hoy).days <= 7
    ]
    sanos = [
        l for l in Lote.query.all()
        if (l.fecha_vencimiento - hoy).days > 7
    ]
    assert vencidos, "debe haber lotes ya vencidos para alimentar las alertas"
    assert proximos, "debe haber lotes próximos a vencer"
    assert sanos, "debe haber lotes con vencimiento saludable"


def test_hay_movimientos_de_entrada_y_salida(sembrados):
    entradas = Movimiento.query.filter_by(tipo="entrada").count()
    salidas = Movimiento.query.filter_by(tipo="salida").count()
    assert entradas > 0
    assert salidas > 0


def test_hay_stock_bajo_y_alertas(sembrados):
    bajos = [a for a in Alimento.query.all() if a.stock_bajo]
    assert bajos, "debe haber alimentos con stock bajo para las alertas"


def test_idempotente(app):
    generar_datos_demo()
    n1 = (Alimento.query.count(), Lote.query.count(), Movimiento.query.count())
    generar_datos_demo()
    n2 = (Alimento.query.count(), Lote.query.count(), Movimiento.query.count())
    assert n1 == n2, "llamar dos veces sin --forzar no debe duplicar datos"


def test_forzar_regenera_limpiamente(app):
    generar_datos_demo()
    primer_lote = Lote.query.count()
    generar_datos_demo(forzar=True)
    assert Alimento.query.count() == len(ALIMENTOS_DEMO)
    assert Lote.query.count() == primer_lote
    assert existen_datos_demo()


def test_cli_seed_demo(runner):
    resultado = runner.invoke(args=["seed-demo"])
    assert resultado.exit_code == 0
    assert "Datos de simulación sembrados" in resultado.output
    assert Alimento.query.count() == len(ALIMENTOS_DEMO)


def test_cli_seed_demo_idempotente(runner):
    runner.invoke(args=["seed-demo"])
    resultado = runner.invoke(args=["seed-demo"])
    assert resultado.exit_code == 0
    assert "Ya existen datos" in resultado.output
    assert Alimento.query.count() == len(ALIMENTOS_DEMO)


def test_cli_seed_demo_forzar(runner):
    runner.invoke(args=["seed-demo"])
    resultado = runner.invoke(args=["seed-demo", "--forzar"])
    assert resultado.exit_code == 0
    assert "Datos de simulación sembrados" in resultado.output


def test_ruta_cargar_datos_admin(cliente_autenticado):
    resp = cliente_autenticado.post("/demo/datos", data={"accion": "cargar"})
    assert resp.status_code == 302
    assert Alimento.query.count() == len(ALIMENTOS_DEMO)


def test_ruta_regenerar_admin(cliente_autenticado):
    from app.extensions import db
    from app.models import Categoria

    # agregar un alimento extra para comprobar que regenerar lo elimina
    categoria = Categoria.query.filter_by(nombre="granos").first()
    extra = Alimento(
        codigo="TMP999", nombre="Temporal", categoria_id=categoria.id,
        unidad_medida="kg", stock_actual=1, stock_minimo=1,
    )
    db.session.add(extra)
    db.session.commit()
    cliente_autenticado.post("/demo/datos", data={"accion": "cargar"})
    resp = cliente_autenticado.post("/demo/datos", data={"accion": "regenerar"})
    assert resp.status_code == 302
    assert Alimento.query.count() == len(ALIMENTOS_DEMO)
    assert not Alimento.query.filter_by(codigo="TMP999").first()


def test_ruta_cargar_datos_bloquea_no_admin(client, encargado):
    from tests.conftest import login

    login(client, "encargado", "enc123456")
    resp = client.post("/demo/datos", data={"accion": "cargar"})
    assert resp.status_code == 302
    assert Alimento.query.count() == 0
