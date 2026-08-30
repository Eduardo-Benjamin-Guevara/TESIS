"""Servicio de datos de simulación (Sprint 7).

Genera un conjunto realista de alimentos, lotes con distintas fechas de
vencimiento y movimientos históricos para poder demostrar y probar todas las
funcionalidades del sistema (gráficos, alertas, notificaciones, reportes)
sin necesidad de cargar datos a mano.

El proceso es **idempotente** por defecto: si ya existen alimentos sembrados,
no hace nada salvo que se solicite `forzar=True`, en cuyo caso elimina los
datos de simulación previos y los vuelve a crear.
"""
import logging
import random
from datetime import date, timedelta

from app.extensions import db
from app.models.alimento import Alimento
from app.models.lote import Lote
from app.models.movimiento import Movimiento, TipoMovimiento
from app.models.usuario import RolUsuario, Usuario

logger = logging.getLogger(__name__)

# Semilla fija para que la simulación sea reproducible en cada entorno.
SEMILLA = 1488
random.seed(SEMILLA)

USUARIO_DEMO = "demo"
PASSWORD_DEMO = "demo123"


# Catálogo de alimentos de demostración por categoría.
# Cada alimento define: código, nombre, unidad, stock mínimo, descripción y
# una lista de lotes con:
#   dias_edad    -> días transcurridos desde el ingreso (>=0)
#   dias_venc    -> días de vida útil del lote (vencimiento = ingreso + dias_venc)
#   qty_entrada  -> cantidad inicial recibida
#   qty_restante -> cantidad que queda (consumo = entrada - restante)
ALIMENTOS_DEMO = [
    # Granos
    {
        "categoria": "granos", "codigo": "ARR001", "nombre": "Arroz",
        "unidad": "kg", "stock_minimo": 5, "descripcion": "Arroz grano largo, saco de 50 kg.",
        "lotes": [
            {"dias_edad": 60, "dias_venc": 150, "qty_entrada": 25, "qty_restante": 14},
            {"dias_edad": 20, "dias_venc": 150, "qty_entrada": 15, "qty_restante": 15},
        ],
    },
    {
        "categoria": "granos", "codigo": "FID002", "nombre": "Fideos",
        "unidad": "paq", "stock_minimo": 8, "descripcion": "Fideos de sémola, paquete 500 g.",
        "lotes": [
            {"dias_edad": 45, "dias_venc": 120, "qty_entrada": 30, "qty_restante": 6},
        ],
    },
    {
        "categoria": "granos", "codigo": "LEN003", "nombre": "Lentejas",
        "unidad": "kg", "stock_minimo": 3, "descripcion": "Lentejas secas seleccionadas.",
        "lotes": [
            {"dias_edad": 30, "dias_venc": 180, "qty_entrada": 10, "qty_restante": 9},
        ],
    },
    {
        "categoria": "granos", "codigo": "AZU004", "nombre": "Azúcar rubia",
        "unidad": "kg", "stock_minimo": 4, "descripcion": "Azúcar rubia, bolsa de 5 kg.",
        "lotes": [
            {"dias_edad": 55, "dias_venc": 200, "qty_entrada": 12, "qty_restante": 10},
        ],
    },
    # Lácteos
    {
        "categoria": "lacteos", "codigo": "LEC001", "nombre": "Leche evaporada",
        "unidad": "lata", "stock_minimo": 10, "descripcion": "Leche evaporada entera en lata 400 g.",
        "lotes": [
            {"dias_edad": 40, "dias_venc": 30, "qty_entrada": 40, "qty_restante": 22},
            {"dias_edad": 10, "dias_venc": 180, "qty_entrada": 30, "qty_restante": 30},
        ],
    },
    {
        "categoria": "lacteos", "codigo": "QUE002", "nombre": "Queso fresco",
        "unidad": "kg", "stock_minimo": 2, "descripcion": "Queso fresco de vaca.",
        "lotes": [
            {"dias_edad": 8, "dias_venc": 5, "qty_entrada": 6, "qty_restante": 4},
        ],
    },
    {
        "categoria": "lacteos", "codigo": "YOG003", "nombre": "Yogurt",
        "unidad": "unid", "stock_minimo": 15, "descripcion": "Yogurt de fresa 180 ml.",
        "lotes": [
            {"dias_edad": 12, "dias_venc": 3, "qty_entrada": 30, "qty_restante": 18},
        ],
    },
    # Carnes
    {
        "categoria": "carnes", "codigo": "POL001", "nombre": "Pollo",
        "unidad": "kg", "stock_minimo": 3, "descripcion": "Pollo entero refrigerado.",
        "lotes": [
            {"dias_edad": 4, "dias_venc": 4, "qty_entrada": 8, "qty_restante": 5},
        ],
    },
    {
        "categoria": "carnes", "codigo": "RES002", "nombre": "Carne de res",
        "unidad": "kg", "stock_minimo": 2, "descripcion": "Carne molida de res.",
        "lotes": [
            {"dias_edad": 2, "dias_venc": 3, "qty_entrada": 6, "qty_restante": 4},
        ],
    },
    {
        "categoria": "carnes", "codigo": "PES003", "nombre": "Pescado fresco",
        "unidad": "kg", "stock_minimo": 2, "descripcion": "Pescado de río fresco.",
        "lotes": [
            {"dias_edad": 1, "dias_venc": 1, "qty_entrada": 5, "qty_restante": 3},
        ],
    },
    # Frutas
    {
        "categoria": "frutas", "codigo": "MAN001", "nombre": "Manzana",
        "unidad": "kg", "stock_minimo": 3, "descripcion": "Manzana roja de mesa.",
        "lotes": [
            {"dias_edad": 6, "dias_venc": 8, "qty_entrada": 10, "qty_restante": 6},
        ],
    },
    {
        "categoria": "frutas", "codigo": "PLA002", "nombre": "Plátano de seda",
        "unidad": "racimo", "stock_minimo": 2, "descripcion": "Plátano de seda, racimo.",
        "lotes": [
            {"dias_edad": 3, "dias_venc": 6, "qty_entrada": 5, "qty_restante": 4},
        ],
    },
    {
        "categoria": "frutas", "codigo": "NAR003", "nombre": "Naranja",
        "unidad": "kg", "stock_minimo": 3, "descripcion": "Naranja dulce para jugo.",
        "lotes": [
            {"dias_edad": 9, "dias_venc": 12, "qty_entrada": 8, "qty_restante": 5},
        ],
    },
    # Verduras
    {
        "categoria": "verduras", "codigo": "PAP001", "nombre": "Papa amarilla",
        "unidad": "kg", "stock_minimo": 10, "descripcion": "Papa amarilla Tumbay.",
        "lotes": [
            {"dias_edad": 15, "dias_venc": 20, "qty_entrada": 20, "qty_restante": 12},
        ],
    },
    {
        "categoria": "verduras", "codigo": "CEB002", "nombre": "Cebolla roja",
        "unidad": "kg", "stock_minimo": 5, "descripcion": "Cebolla roja de cabeza.",
        "lotes": [
            {"dias_edad": 7, "dias_venc": 14, "qty_entrada": 12, "qty_restante": 9},
        ],
    },
    {
        "categoria": "verduras", "codigo": "ZAN003", "nombre": "Zanahoria",
        "unidad": "kg", "stock_minimo": 4, "descripcion": "Zanahoria fresca.",
        "lotes": [
            {"dias_edad": 5, "dias_venc": 10, "qty_entrada": 8, "qty_restante": 6},
        ],
    },
    {
        "categoria": "verduras", "codigo": "TOM004", "nombre": "Tomate",
        "unidad": "kg", "stock_minimo": 3, "descripcion": "Tomate italiano.",
        "lotes": [
            {"dias_edad": 3, "dias_venc": 5, "qty_entrada": 7, "qty_restante": 5},
        ],
    },
    # Abarrotes
    {
        "categoria": "abarrotes", "codigo": "ACE001", "nombre": "Aceite vegetal",
        "unidad": "botella", "stock_minimo": 4, "descripcion": "Aceite vegetal 1 L.",
        "lotes": [
            {"dias_edad": 50, "dias_venc": 240, "qty_entrada": 12, "qty_restante": 7},
        ],
    },
    {
        "categoria": "abarrotes", "codigo": "ATU002", "nombre": "Atún en conserva",
        "unidad": "lata", "stock_minimo": 8, "descripcion": "Atún en aceite, lata 170 g.",
        "lotes": [
            {"dias_edad": 35, "dias_venc": 90, "qty_entrada": 25, "qty_restante": 11},
        ],
    },
    {
        "categoria": "abarrotes", "codigo": "SAL003", "nombre": "Sal de mesa",
        "unidad": "kg", "stock_minimo": 2, "descripcion": "Sal yodada fina.",
        "lotes": [
            {"dias_edad": 70, "dias_venc": 300, "qty_entrada": 5, "qty_restante": 5},
        ],
    },
    {
        "categoria": "abarrotes", "codigo": "LCP004", "nombre": "Leche en polvo",
        "unidad": "bolsa", "stock_minimo": 6, "descripcion": "Leche en polvo entera 400 g.",
        "lotes": [
            {"dias_edad": 25, "dias_venc": 60, "qty_entrada": 20, "qty_restante": 14},
        ],
    },
    # Bebidas
    {
        "categoria": "bebidas", "codigo": "JUG001", "nombre": "Jugo de naranja",
        "unidad": "botella", "stock_minimo": 5, "descripcion": "Jugo natural 1 L.",
        "lotes": [
            {"dias_edad": 10, "dias_venc": 15, "qty_entrada": 18, "qty_restante": 9},
        ],
    },
    {
        "categoria": "bebidas", "codigo": "AGU002", "nombre": "Agua de mesa",
        "unidad": "botella", "stock_minimo": 12, "descripcion": "Agua sin gas 625 ml.",
        "lotes": [
            {"dias_edad": 20, "dias_venc": 180, "qty_entrada": 40, "qty_restante": 26},
        ],
    },
    # Otros
    {
        "categoria": "otros", "codigo": "GAL001", "nombre": "Galletas integrales",
        "unidad": "paq", "stock_minimo": 6, "descripcion": "Galletas integrales paquete 8.",
        "lotes": [
            {"dias_edad": 15, "dias_venc": 45, "qty_entrada": 20, "qty_restante": 13},
        ],
    },
    {
        "categoria": "otros", "codigo": "CAF002", "nombre": "Café molido",
        "unidad": "kg", "stock_minimo": 1, "descripcion": "Café molido 500 g.",
        "lotes": [
            {"dias_edad": 30, "dias_venc": 120, "qty_entrada": 3, "qty_restante": 2},
        ],
    },
    {
        "categoria": "otros", "codigo": "CHO003", "nombre": "Chocolate de taza",
        "unidad": "paq", "stock_minimo": 3, "descripcion": "Chocolate para taza, pastillas.",
        "lotes": [
            {"dias_edad": 18, "dias_venc": 200, "qty_entrada": 10, "qty_restante": 8},
        ],
    },
]


def _obtener_o_crear_usuario_demo() -> Usuario:
    """Devuelve el usuario de demostración, creándolo si no existe."""
    usuario = Usuario.query.filter_by(usuario=USUARIO_DEMO).first()
    if usuario is None:
        usuario = Usuario(
            nombre="Usuario de Demostración",
            usuario=USUARIO_DEMO,
            rol=RolUsuario.ENCARGADO,
            activo=True,
        )
        usuario.set_password(PASSWORD_DEMO)
        db.session.add(usuario)
        logger.info("Usuario demo creado: %s", USUARIO_DEMO)
    return usuario


def existen_datos_demo() -> bool:
    """Indica si ya existen alimentos (asume que implican datos de simulación)."""
    return db.session.query(Alimento.id).first() is not None


def _eliminar_datos_simulacion() -> None:
    """Borra todos los datos de simulación (alimentos, lotes y movimientos)."""
    Movimiento.query.delete()
    Lote.query.delete()
    Alimento.query.delete()
    Usuario.query.filter_by(usuario=USUARIO_DEMO).delete()
    db.session.commit()


def generar_datos_demo(forzar: bool = False) -> dict:
    """Genera los datos de simulación.

    Si ya existen alimentos y `forzar` es False, no hace nada (idempotente).

    Devuelve un resumen con las cantidades creadas.
    """
    resumen_previo = {
        "alimentos": Alimento.query.count(),
        "lotes": Lote.query.count(),
        "movimientos": Movimiento.query.count(),
        "creado": False,
    }
    if not forzar and existen_datos_demo():
        return resumen_previo

    if forzar:
        _eliminar_datos_simulacion()
        # Limpia el mapa de identidad para regenerar limpiamente sin advertencias
        db.session.remove()

    # Garantizar categorías por defecto
    from app.services.init_services import sembrar_categorias

    sembrar_categorias()

    usuario_demo = _obtener_o_crear_usuario_demo()
    db.session.flush()

    from datetime import datetime
    from app.models.categoria import Categoria

    lotes_creados = 0
    movimientos_creados = 0

    for item in ALIMENTOS_DEMO:
        categoria = Categoria.query.filter_by(nombre=item["categoria"]).first()
        alimento = Alimento(
            codigo=item["codigo"],
            nombre=item["nombre"],
            categoria_id=categoria.id if categoria else None,
            unidad_medida=item["unidad"],
            descripcion=item["descripcion"],
            stock_minimo=item["stock_minimo"],
            stock_actual=0,
        )
        db.session.add(alimento)
        db.session.flush()

        # Lista de movimientos del alimento para luego calcular stock_resultante
        movs_del_alimento = []
        hoy = date.today()

        for lote in item["lotes"]:
            ingreso = hoy - timedelta(days=lote["dias_edad"])
            vencimiento = ingreso + timedelta(days=lote["dias_venc"])
            resto = float(lote["qty_restante"])
            entrada = float(lote["qty_entrada"])

            reg_lote = Lote(
                codigo=f"{item['codigo']}-{lotes_creados + 1:02d}",
                alimento_id=alimento.id,
                fecha_ingreso=ingreso,
                fecha_vencimiento=vencimiento,
                cantidad=resto,
                activo=True,
            )
            db.session.add(reg_lote)
            db.session.flush()
            lotes_creados += 1

            # Movimiento de entrada (compra)
            fecha_entrada = datetime.combine(ingreso, datetime.min.time())
            m_entrada = Movimiento(
                tipo=TipoMovimiento.ENTRADA,
                alimento_id=alimento.id,
                lote_id=reg_lote.id,
                cantidad=entrada,
                stock_resultante=0,
                motivo="Compra / donación",
                usuario_id=usuario_demo.id,
                fecha=fecha_entrada,
            )
            db.session.add(m_entrada)
            movimientos_creados += 1
            movs_del_alimento.append((fecha_entrada, m_entrada, +entrada))

            # Movimiento(s) de salida (consumo) si hubo consumo
            consumo = entrada - resto
            if consumo > 0:
                # Fecha de salida a mitad de la vida útil del lote
                fecha_salida = ingreso + timedelta(days=int(lote["dias_venc"] / 2))
                fecha_salida_dt = datetime.combine(fecha_salida, datetime.min.time())
                m_salida = Movimiento(
                    tipo=TipoMovimiento.SALIDA,
                    alimento_id=alimento.id,
                    lote_id=reg_lote.id,
                    cantidad=consumo,
                    stock_resultante=0,
                    motivo="Consumo / Preparación",
                    usuario_id=usuario_demo.id,
                    fecha=fecha_salida_dt,
                )
                db.session.add(m_salida)
                movimientos_creados += 1
                movs_del_alimento.append((fecha_salida_dt, m_salida, -consumo))

        # Calcular stock_resultante de forma coherente (orden cronológico)
        movs_del_alimento.sort(key=lambda x: x[0])
        acumulado = 0
        for _fecha, mov, delta in movs_del_alimento:
            acumulado += delta
            mov.stock_resultante = acumulado

        # El stock actual final es el acumulado tras el último movimiento
        alimento.stock_actual = acumulado

    db.session.commit()

    return {
        "alimentos": Alimento.query.count(),
        "lotes": Lote.query.count(),
        "movimientos": Movimiento.query.count(),
        "usuario_demo": USUARIO_DEMO,
        "creado": True,
    }
