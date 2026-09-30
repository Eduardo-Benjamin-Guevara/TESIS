"""Servicio de inteligencia artificial para el sistema.

Un asistente conversacional que entiende preguntas en español y responde con
datos REALES del inventario (stock, vencimientos, alertas, recomendaciones,
movimientos, categorías) usando los servicios existentes del dominio.

Incluye tres componentes:
1. **Clasificador de intenciones entrenado**: un modelo TF-IDF + similitud de
   coseno (implementado sin dependencias pesadas para funcionar en serverless)
   entrenado con un corpus de frases en español específicas del dominio. La
   función :func:`entrenar` construye los vectores y las estadísticas del
   modelo; :func:`clasificar` los usa para predecir la intención de una
   consulta nueva.
2. **Base de conocimiento**: el corpus de intenciones más una sección de
   "cómo usar el sistema" que cubre todas las funciones del software.
3. **Conector a IA externa (opcional)**: si se configura `IA_API_KEY` (API
   compatible con OpenAI/Chat Completions), la consulta se envía a la IA
   externa con un resumen del inventario como contexto; si falla o no está
   configurada, se usa el asistente integrado (modelo entrenado).
"""
import itertools
import math
import re
from collections import Counter
from datetime import date

from flask import current_app


class ErrorIA(Exception):
    """Error de la inteligencia artificial (conexión externa, etc.)."""


# ---------------------------------------------------------------------------
# Corpus de entrenamiento (intenciones y frases de ejemplo en español)
# ---------------------------------------------------------------------------
CORPUS = {
    "saludo": [
        "hola",
        "buenos dias",
        "buenas tardes",
        "buenas noches",
        "hola asistente",
        "hola como estas",
        "hey",
        "que tal",
    ],
    "despedida": [
        "adios",
        "chao",
        "hasta luego",
        "nos vemos",
        "hasta pronto",
        "me voy",
    ],
    "gracias": [
        "gracias",
        "muchas gracias",
        "te agradezco",
        "gracias por tu ayuda",
        "muy amable",
    ],
    "ayuda": [
        "que puedes hacer",
        "ayuda",
        "como funciona el asistente",
        "que sabes hacer",
        "para que sirves",
        "cuales son tus funciones",
        "dime que puedo preguntarte",
        "ayudame",
        "que funciones tienes",
    ],
    "resumen": [
        "resumen del inventario",
        "como esta mi inventario",
        "estado del inventario",
        "cuantos alimentos hay",
        "cuantos alimentos hay registrados",
        "dame un resumen",
        "situacion actual",
        "como vamos con el inventario",
        "stock total",
        "total de alimentos",
        "que me puedes contar del sistema",
        "indicadores generales",
        "muestrame los indicadores",
    ],
    "stock_bajo": [
        "que alimentos tienen stock bajo",
        "stock bajo",
        "que tengo poco",
        "me falta stock",
        "que alimentos estan escasos",
        "alimentos agotados",
        "que me falta",
        "productos con stock bajo",
        "cuales estan por debajo del minimo",
        "que alimentos necesitan reposicion",
        "falta inventario",
        "alimentos con stock critico",
    ],
    "vencimiento": [
        "que vence pronto",
        "proximos a vencer",
        "fechas de vencimiento",
        "cuando vence",
        "que esta por vencer",
        "lotes por vencer",
        "alimentos cerca de vencer",
        "que caduca",
        "productos por caducar",
        "que vence esta semana",
        "prontos a vencer",
    ],
    "vencidos": [
        "que alimentos estan vencidos",
        "vencidos",
        "ya caducados",
        "alimentos vencidos",
        "productos caducados",
        "que ya vencio",
        "cuales estan vencidos",
        "alimentos que vencieron",
    ],
    "recomendaciones": [
        "que debo comprar",
        "recomendaciones de compra",
        "que debo reabastecer",
        "que comprar",
        "sugerencias de compra",
        "que me recomiendas comprar",
        "lista de compras",
        "que productos faltan comprar",
        "que reponer",
    ],
    "categorias": [
        "stock por categoria",
        "cuantas categorias hay",
        "por categorias",
        "cuantas categorias existen",
        "que categorias tiene el inventario",
        "como esta el stock por categoria",
        "categorias de alimentos",
    ],
    "alimento": [
        "informacion de un alimento",
        "dime de un alimento",
        "buscar alimento",
        "cuanto stock tiene un alimento",
        "busca un alimento",
        "cuentame de",
        "hablame de",
        "stock de un alimento",
        "detalle de un alimento",
        "buscar por codigo",
    ],
    "movimientos": [
        "ultimas entradas y salidas",
        "movimientos recientes",
        "historial de movimientos",
        "que entradas hubo",
        "ultimas salidas",
        "actividad reciente",
        "ultimos movimientos",
        "cuantas entradas hay",
        "cuantas salidas hay",
    ],
    "alertas": [
        "cuantas alertas hay",
        "alertas activas",
        "tengo alertas",
        "ver alertas",
        "cuantas alertas tengo",
        "hay alertas criticas",
        "resumen de alertas",
    ],
    "sistema": [
        "como registro un alimento",
        "como agrego una entrada",
        "como hago una salida",
        "como crear un usuario",
        "como exportar reportes",
        "como se usa el sistema",
        "como funciona el sistema",
        "registrar alimento",
        "agregar lote",
        "agregar categoria",
        "como hago",
        "como se hace",
        "guia del sistema",
        "manual del sistema",
        "como actualizo un alimento",
        "como marco las notificaciones",
    ],
}

# Términos vacíos frecuentes del español (se ignoran al vectorizar)
STOPWORDS = {
    "de", "la", "el", "los", "las", "un", "una", "unos", "unas", "del", "al",
    "y", "o", "u", "que", "como", "cual", "cuales", "por", "para", "con",
    "en", "a", "es", "se", "su", "sus", "me", "mi", "te", "tu", "le", "lo",
    "ha", "he", "han", "hay", "tiene", "tienen", "esta", "estan", "en",
    "sobre", "entre", "todos", "todas", "toda", "todo", "mas", "menos",
    "muy", "bien", "mal", "ahora", "cuando", "donde", "quiero", "puedes",
    "puedo", "quieres", "dime", "dame", "ver", "mostrar", "muestrame",
    "buscar", "busca", "cuanto", "cuanta", "cuantos", "cuantas", "que",
}


def _tokenizar(texto: str) -> list[str]:
    """Normaliza y separa un texto en tokens sin términos vacíos."""
    limpio = re.sub(r"[^\w\sáéíóúüñ]", " ", texto.lower())
    return [t for t in limpio.split() if t and t not in STOPWORDS]


# ---------------------------------------------------------------------------
# Entrenamiento del modelo (TF-IDF + similitud de coseno)
# ---------------------------------------------------------------------------
def _df_termino(docs: list[list[str]]) -> dict[str, int]:
    """Frecuencia documental: cuántos documentos contienen cada término."""
    df: dict[str, int] = {}
    for doc in docs:
        for t in set(doc):
            df[t] = df.get(t, 0) + 1
    return df


def _tfidf(doc: list[str], df: dict[str, int], n_docs: int) -> Counter:
    """Vector TF-IDF de un documento."""
    freq = Counter(doc)
    vector = Counter()
    for t, f in freq.items():
        idf = math.log((1 + n_docs) / (1 + df.get(t, 0))) + 1
        vector[t] = f * idf
    return vector


def _normalizar(vector: Counter) -> Counter:
    """Divide el vector por su norma (para similitud de coseno)."""
    norma = math.sqrt(sum(v * v for v in vector.values())) or 1.0
    return Counter({t: v / norma for t, v in vector.items()})


def _similitud_coseno(a: Counter, b: Counter) -> float:
    """Similitud del coseno entre dos vectores TF-IDF normalizados."""
    productos = set(a) & set(b)
    return sum(a[t] * b[t] for t in productos)


def entrenar() -> dict:
    """Entrena y devuelve el modelo (vector TF-IDF por intención).

    El modelo se construye a partir del corpus de ejemplos. Se devuelve un
    diccionario con, para cada intención, la lista de vectores TF-IDF
    normalizados de sus frases de ejemplo.
    """
    docs_todos = {i: [_tokenizar(f) for f in frases] for i, frases in CORPUS.items()}
    todas: list[list[str]] = []
    for docs in docs_todos.values():
        todas.extend(docs)
    n_docs = len(todas)
    df = _df_termino(todas)

    modelo = {}
    for intencion, docs in docs_todos.items():
        modelo[intencion] = [
            _normalizar(_tfidf(doc, df, n_docs)) for doc in docs
        ]
    return modelo


# El modelo se entrena una sola vez por proceso (cacheado a nivel de módulo)
_modelo_cache = None


def obtener_modelo() -> dict:
    """Devuelve el modelo entrenado, entrenándolo la primera vez."""
    global _modelo_cache
    if _modelo_cache is None:
        _modelo_cache = entrenar()
    return _modelo_cache


def clasificar(texto: str) -> tuple[str, float]:
    """Clasifica una consulta y devuelve ``(intención, confianza)``.

    La confianza es la máxima similitud del coseno entre la consulta y las
    frases de ejemplo de cada intención. Si la coincidencia es demasiado
    débil (por debajo del umbral), se devuelve ``"no_identificada"``.
    """
    tokens = _tokenizar(texto)
    if not tokens:
        return "ayuda", 0.0
    modelo = obtener_modelo()
    df = _df_termino(list(itertools.chain(*modelo.values())))
    n_docs = sum(len(v) for v in modelo.values())
    q = _normalizar(_tfidf(tokens, df, n_docs))

    mejor_intencion = "ayuda"
    mejor_confianza = 0.0
    for intencion, ejemplos in modelo.items():
        if intencion == "ayuda":
            continue
        for ej in ejemplos:
            sim = _similitud_coseno(q, ej)
            if sim > mejor_confianza:
                mejor_confianza = sim
                mejor_intencion = intencion

    # Comprobamos también "ayuda" contra los demás
    for ej in modelo.get("ayuda", []):
        sim = _similitud_coseno(q, ej)
        if sim > mejor_confianza:
            mejor_confianza = sim
            mejor_intencion = "ayuda"

    if mejor_confianza < 0.12:
        return "no_identificada", mejor_confianza
    return mejor_intencion, mejor_confianza


# ---------------------------------------------------------------------------
# Base de conocimiento: guía de uso del sistema
# ---------------------------------------------------------------------------
GUIA_SISTEMA = {
    "registrar alimento": (
        "Para registrar un alimento ve a **Alimentos → Nuevo alimento**. "
        "Completa código (se normaliza en mayúsculas), nombre, categoría, "
        "unidad de medida, stock inicial y stock mínimo."
    ),
    "entrada": (
        "Para registrar una **entrada de inventario** (recibo mercadería): "
        "**Movimientos → Entradas**, elige el alimento, la cantidad y "
        "guardas. El stock se actualiza automáticamente."
    ),
    "salida": (
        "Para registrar una **salida** (consumo o despacho): "
        "**Movimientos → Salidas**, elige el alimento, la cantidad y guardas."
    ),
    "lote/vencimiento": (
        "Registra el lote y su **fecha de vencimiento** en "
        "**Fechas de vencimiento → Nuevo lote**. El sistema calcula alertas "
        "de vencimiento automáticamente según los días restantes."
    ),
    "categoría": (
        "Para crear/modificar categorías usa **Categorías** y su botón "
        "**Nueva categoría**."
    ),
    "usuario": (
        "Solo el administrador puede crear usuarios: "
        "**Administración → Usuarios**."
    ),
    "reporte/exportación": (
        "En **Monitoreo → Reportes** puedes exportar el inventario a CSV o "
        "Excel con el botón **Exportar**."
    ),
    "qr": (
        "Cada alimento tiene un **código QR** (ver el detalle del alimento) "
        "con la información del producto y sus lotes para trazabilidad."
    ),
    "trazabilidad": (
        "El sistema reconstruye el **historial completo** de un alimento "
        "(todas sus entradas y salidas) desde el detalle del alimento."
    ),
    "alertas": (
        "El sistema genera alertas por **vencimiento** y por **stock bajo**, "
        "clasificadas en crítica, alta y media. Se ven en **Alertas** y en "
        "la campana de notificaciones."
    ),
    "recomendaciones": (
        "En **Monitoreo → Recomendaciones** el sistema sugiere qué comprar "
        "en base al stock bajo, priorizando lo más urgente."
    ),
}


def _conseguir_guia(texto: str) -> str:
    """Busca una entrada de la guía según palabras clave de la consulta."""
    texto_l = texto.lower()
    coincidencias = []
    claves = {
        "registrar alimento": ["registrar alimento", "nuevo alimento", "crear alimento", "alta alimento"],
        "entrada": ["entrada", "recibo", "agregar entrada", "ingreso"],
        "salida": ["salida", "consumo", "despacho", "egreso", "quitar"],
        "lote/vencimiento": ["lote", "vencimiento", "fecha de caducidad", "caducidad"],
        "categoría": ["categoria", "categorias"],
        "usuario": ["usuario", "usuarios", "crear usuario", "alta usuario"],
        "reporte/exportación": ["exportar", "reporte", "excel", "csv", "descargar"],
        "qr": ["qr", "codigo qr"],
        "trazabilidad": ["trazabilidad", "historial del alimento", "de donde viene"],
        "alertas": ["alerta", "alertas", "notificaciones"],
        "recomendaciones": ["recomendar", "recomendacion", "comprar", "reabastecer"],
    }
    for seccion, palabras in claves.items():
        if any(p in texto_l for p in palabras):
            coincidencias.append(GUIA_SISTEMA[seccion])
    if coincidencias:
        return "\n".join(dict.fromkeys(coincidencias))
    return (
        "Puedo ayudarte con el uso de todo el sistema: registrar alimentos, "
        "categorías, lotes, entradas/salidas, crear usuarios, exportar "
        "reportes, códigos QR, trazabilidad, alertas y recomendaciones. "
        "Escríbeme qué necesitas hacer."
    )


# ---------------------------------------------------------------------------
# Generación de respuestas con datos reales del sistema
# ---------------------------------------------------------------------------
def _resumen_inventario() -> str:
    from app.services import reportes_service

    k = reportes_service.kpis()
    lineas = [
        "**Resumen del inventario** 📊",
        f"- Alimentos activos: **{k['total_alimentos']}**",
        f"- Categorías: **{k['total_categorias']}**",
        f"- Stock total: **{k['stock_total']:.2f}** unidades",
        f"- Con stock: **{k['con_stock']}** / {k['total_alimentos']}",
        f"- Stock bajo: **{k['stock_bajo']}**",
        f"- Próximos a vencer: **{k['proximos_vencer']}**",
        f"- Vencidos: **{k['vencidos']}**",
        f"- Movimientos: **{k['entradas']}** entradas, **{k['salidas']}** salidas",
        f"- Alertas activas: **{k['alertas_activas']}**",
    ]
    return "\n".join(lineas)


def _respuesta_stock_bajo() -> str:
    from app.services import alertas_service

    items = alertas_service.stock_bajo()
    if not items:
        return "👍 No hay alimentos con stock bajo. El inventario está dentro de los mínimos."
    lineas = ["**Alimentos con stock bajo:**", ""]
    for a in items:
        icono = "🔴" if a["nivel"] == "critica" else ("🟠" if a["nivel"] == "alta" else "🟡")
        lineas.append(
            f"- {icono} {a['alimento'].nombre} ({a['alimento'].codigo}): "
            f"{a['stock']:g} de mínimo {a['minimo']:g}"
        )
    lineas.append("")
    lineas.append("Sugerencia: revisa **Monitoreo → Recomendaciones** para saber qué comprar.")
    return "\n".join(lineas)


def _respuesta_vencimientos() -> str:
    from app.services import alertas_service

    items = alertas_service.proximos_a_vencer()
    no_vencidos = [x for x in items if x["dias"] >= 0]
    if not no_vencidos:
        return "👍 Ningún lote está próximo a vencer en los próximos días."
    lineas = ["**Lotes próximos a vencer:**", ""]
    for x in sorted(no_vencidos, key=lambda i: i["dias"]):
        nivel = "🔴" if x["nivel"] == "critica" else ("🟠" if x["nivel"] == "alta" else "🟡")
        lineas.append(
            f"- {nivel} {x['alimento'].nombre} ({x['lote'].codigo or 'Lote'}): "
            f"vence en **{x['dias']} día(s)** ({x['fecha_vencimiento']:%d/%m/%Y}), "
            f"{x['cantidad']:g} ud."
        )
    return "\n".join(lineas)


def _respuesta_vencidos() -> str:
    from app.services import alertas_service

    items = [x for x in alertas_service.proximos_a_vencer() if x["dias"] < 0]
    if not items:
        return "👍 No hay alimentos vencidos."
    lineas = ["**Alimentos vencidos:**", ""]
    for x in items:
        lineas.append(
            f"- 🔴 {x['alimento'].nombre} ({x['lote'].codigo or 'Lote'}): "
            f"venció hace {abs(x['dias'])} día(s)"
        )
    lineas.append("")
    lineas.append("⚠️ Retíralos del inventario registrando una salida de descarte.")
    return "\n".join(lineas)


def _respuesta_recomendaciones() -> str:
    from app.services import recomendaciones_service

    items = recomendaciones_service.recomendaciones()
    if not items:
        return "🎉 No hay recomendaciones de compra: todo el inventario está suficiente."
    lineas = ["**Recomendaciones de compra:**", ""]
    for r in items[:10]:
        etiqueta = "🔴 URGENTE" if r["urgente"] else "🟠"
        lineas.append(
            f"- {etiqueta} {r['alimento'].nombre} ({r['alimento'].codigo}): "
            f"tienes {r['actual']:g}, mínimo {r['minimo']:g}. "
            f"Compra ~**{r['cantidad_sugerida']:g}** ud."
        )
    return "\n".join(lineas)


def _respuesta_categorias() -> str:
    from app.services import reportes_service

    filas = reportes_service.reporte_por_categoria()
    if not filas:
        return "No hay categorías registradas todavía."
    lineas = ["**Stock por categoría:**", ""]
    for f in filas:
        lineas.append(
            f"- **{f['categoria'].nombre.capitalize()}**: {f['cantidad']} alimento(s), "
            f"stock {f['stock']:g}"
        )
    return "\n".join(lineas)


def _buscar_alimento(texto: str):
    """Busca alimentos/categorías nombrados en la consulta."""
    from app.services import alimento_service, categoria_service

    tokens = _tokenizar(texto)
    if not tokens:
        return None, None

    # Prioridad: coincidencia por nombre completo o código
    todos = alimento_service.listar(incluir_inactivos=False)
    coincidencias = []
    for a in todos:
        nombre_l = a.nombre.lower()
        codigo_l = a.codigo.lower()
        for t in tokens:
            if t == nombre_l or (len(t) >= 4 and (t in nombre_l or t in codigo_l)):
                coincidencias.append(a)
                break
    if len(coincidencias) == 1:
        return coincidencias[0], None

    # Si no hubo coincidencia clara, probar por categorías
    for c in categoria_service.listar():
        c_l = c.nombre.lower()
        if any(t == c_l or (len(t) >= 4 and t in c_l) for t in tokens):
            return None, c
    if coincidencias:
        return coincidencias[0], None
    return None, None


def _respuesta_alimento_especifico(alimento) -> str:
    from app.services import alertas_service, trazabilidad_service

    lineas = [
        f"**{alimento.nombre}** ({alimento.codigo})",
        f"- Categoría: {alimento.categoria if alimento.categoria else '—'}",
        f"- Unidad: {alimento.unidad_medida}",
        f"- Stock actual: **{alimento.stock_actual:g}** (mínimo {alimento.stock_minimo:g})",
    ]
    if alimento.stock_bajo:
        nivel = alertas_service._nivel_stock(alimento)
        icono = "🔴" if nivel == "critica" else "🟠"
        lineas.append(f"- ⚠️ {icono} Stock **bajo**")
    lotes = [l for l in alimento.lotes if l.activo and (l.cantidad or 0) > 0]
    if lotes:
        proximo = min(lotes, key=lambda l: l.fecha_vencimiento)
        dias = (proximo.fecha_vencimiento - date.today()).days
        lineas.append(
            f"- Próximo vencimiento activo: **{proximo.fecha_vencimiento:%d/%m/%Y}**"
            f" (faltan {dias} día(s))"
        )
    datos_trazabilidad = trazabilidad_service.trazabilidad_alimento(alimento.id)
    lineas.append(
        f"- Historial: {len(datos_trazabilidad['movimientos'])} movimiento(s), "
        f"{datos_trazabilidad['total_entradas']:g} entradas / "
        f"{datos_trazabilidad['total_salidas']:g} salidas"
    )
    return "\n".join(lineas)


def _respuesta_movimientos() -> str:
    from app.services import reportes_service

    movs = reportes_service.actividad_reciente(limit=8)
    if not movs:
        return "Aún no hay movimientos registrados."
    lineas = ["**Actividad reciente:**", ""]
    for m in movs:
        signo = "+" if m.es_entrada else "-"
        color = "🟢" if m.es_entrada else "🔵"
        lineas.append(
            f"- {color} {signo}{m.cantidad:g} · {m.alimento.nombre} "
            f"({m.fecha:%d/%m %H:%M})"
        )
    return "\n".join(lineas)


def _respuesta_alertas() -> str:
    from app.services import alertas_service

    a = alertas_service.contar()
    return (
        f"**Alertas activas: {a['total']}**\n"
        f"- 🔴 Críticas: {a['critica']}\n"
        f"- 🟠 Altas: {a['alta']}\n"
        f"- 🟡 Medias: {a['media']}\n\n"
        "Detalle completo en **Alertas**."
    )


_RESPUESTAS_FIJAS = {
    "saludo": "¡Hola! 👋 Soy el asistente inteligente del sistema de control de "
    "alimentos. Pregúntame sobre el inventario, stock bajo, vencimientos, "
    "recomendaciones o cómo usar el sistema.",
    "despedida": "¡Hasta luego! 👋 Si necesitas algo más, aquí estaré.",
    "gracias": "¡De nada! 😊 ¿Necesitas algo más del inventario?",
    "ayuda": (
        "Puedo ayudarte con:\n"
        "- 📊 **Resumen** del inventario\n"
        "- 🟠 **Stock bajo**\n"
        "- 📅 **Próximos a vencer / vencidos**\n"
        "- 🛒 **Recomendaciones de compra**\n"
        "- 🏷️ **Stock por categoría**\n"
        "- 🔎 **Información de un alimento** (por ejemplo: \"cuánto stock hay de avena\")\n"
        "- 📈 **Movimientos y actividad reciente**\n"
        "- ❓ **Cómo usar el sistema** (ej.: \"cómo registro un alimento\")"
    ),
}


# ---------------------------------------------------------------------------
# Conector a IA externa (opcional)
# ---------------------------------------------------------------------------
def _ctx_externo(texto: str) -> str:
    """Prepara un contexto breve del inventario para la IA externa."""
    try:
        return _resumen_inventario()
    except Exception:
        return "Sistema de control de inventario de alimentos de una institución educativa."


def consultar_ia_externa(texto: str) -> str:
    """Consulta una API externa compatible con OpenAI (Chat Completions).

    Requiere las variables de entorno: ``IA_API_KEY``, ``IA_API_URL`` y
    ``IA_API_MODEL``. Si no responden correctamente, se levanta ErrorIA.
    """
    import urllib.request

    clave = current_app.config.get("IA_API_KEY") or ""
    if not clave:
        raise ErrorIA("IA externa no configurada (IA_API_KEY).")
    url = current_app.config.get("IA_API_URL", "https://api.openai.com/v1/chat/completions")
    modelo = current_app.config.get("IA_API_MODEL", "gpt-4o-mini")

    cuerpo = {
        "model": modelo,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Eres el asistente de un sistema web de control de inventario "
                    "de alimentos de una institución educativa (I.E.I. N.° 1488). "
                    "Responde en español, de forma breve y con datos reales.\n\n"
                    f"Contexto del inventario:\n{_ctx_externo(texto)}"
                ),
            },
            {"role": "user", "content": texto},
        ],
        "temperature": 0.4,
        "max_tokens": 500,
    }
    request = urllib.request.Request(
        url,
        data=__import__("json").dumps(cuerpo).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {clave}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as respuesta:
            datos = __import__("json").loads(respuesta.read().decode("utf-8"))
        return datos["choices"][0]["message"]["content"].strip()
    except Exception as exc:  # red, API, formato
        raise ErrorIA(f"No se pudo consultar la IA externa: {exc}") from exc


# ---------------------------------------------------------------------------
# Punto de entrada principal
# ---------------------------------------------------------------------------
def preguntar(texto: str) -> dict:
    """Responde a una consulta del usuario (asistente integrado + externo).

    Devuelve un diccionario con ``respuesta``, ``intencion``, ``confianza``
    y ``origen`` (``"externa"`` o ``"entrenada"``).
    """
    texto = (texto or "").strip()
    if not texto:
        return {
            "respuesta": "Escríbeme una pregunta sobre el inventario.",
            "intencion": "ayuda",
            "confianza": 0.0,
            "origen": "entrenada",
        }

    # 1) Priorizar la IA externa si está configurada
    if (current_app.config.get("IA_API_KEY") or "").strip():
        try:
            return {
                "respuesta": consultar_ia_externa(texto),
                "intencion": "externo",
                "confianza": 1.0,
                "origen": "externa",
            }
        except ErrorIA:
            pass  # cae al asistente integrado

    # 2) Asistente integrado (modelo entrenado)
    intencion, confianza = clasificar(texto)

    if intencion in _RESPUESTAS_FIJAS:
        return {
            "respuesta": _RESPUESTAS_FIJAS[intencion],
            "intencion": intencion,
            "confianza": round(confianza, 3),
            "origen": "entrenada",
        }

    if intencion == "alimento":
        alimento, _categoria = _buscar_alimento(texto)
        if alimento is not None:
            return {
                "respuesta": _respuesta_alimento_especifico(alimento),
                "intencion": "alimento",
                "confianza": round(confianza, 3),
                "origen": "entrenada",
            }

    # Intenciones que consultan datos reales
    generador = {
        "resumen": _resumen_inventario,
        "stock_bajo": _respuesta_stock_bajo,
        "vencimiento": _respuesta_vencimientos,
        "vencidos": _respuesta_vencidos,
        "recomendaciones": _respuesta_recomendaciones,
        "categorias": _respuesta_categorias,
        "movimientos": _respuesta_movimientos,
        "alertas": _respuesta_alertas,
        "sistema": lambda: _conseguir_guia(texto),
    }.get(intencion)

    if generador is not None:
        respuesta = generador()
        if intencion == "sistema" and not any(
            p in texto.lower() for p in ("como", "cómo", "registrar", "crear", "agregar", "exportar", "opciones")
        ):
            respuesta = (
                "**Acerca del sistema**\n\n"
                "Este sistema gestiona el inventario de alimentos: alimentos, "
                "categorías, lotes con fechas de vencimiento, entradas y "
                "salidas, alertas automáticas, notificaciones, reportes "
                "exportables, códigos QR y trazabilidad.\n\n"
                "Pregúntame también **cómo** hacer alguna tarea."
            )
        return {
            "respuesta": respuesta,
            "intencion": intencion,
            "confianza": round(confianza, 3),
            "origen": "entrenada",
        }

    return {
        "respuesta": (
            "🤔 No estoy seguro de haber entendido. Puedes preguntarme por:\n"
            "- el **resumen** del inventario\n"
            "- qué hay con **stock bajo** o **por vencer**\n"
            "- **recomendaciones de compra**\n"
            "- información de un **alimento** o su **categoría**\n"
            "- o cómo **usar el sistema**"
        ),
        "intencion": "no_identificada",
        "confianza": round(confianza, 3),
        "origen": "entrenada",
    }