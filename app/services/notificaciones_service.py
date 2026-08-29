"""Servicio de notificaciones (centro de alertas del usuario).

Construye las notificaciones a partir de las alertas derivadas del inventario
(lotes próximos a vencer y stock bajo) y las marca como leídas por usuario,
persistiendo el reconocimiento en `NotificacionLeida`.
"""
from app.extensions import db
from app.models import NotificacionLeida
from app.services import alertas_service

# Niveles por prioridad (para el peso/color en la interfaz)
PESO_NIVEL = {"critica": 0, "alta": 1, "media": 2}


def _clave(tipo: str, referencia_id: int) -> tuple:
    return (tipo, referencia_id)


def notificaciones_usuario(usuario) -> dict:
    """Devuelve las notificaciones del usuario, con su estado de lectura.

    Retorna: `{"items": [...], "no_leidas": int, "total": int}`.
    Cada item incluye: tipo, nivel, titulo, mensaje, url, icono, leida.
    """
    alertas = alertas_service.todas()
    read = {
        _clave(n.tipo, n.referencia_id)
        for n in NotificacionLeida.query.filter_by(usuario_id=usuario.id).all()
    }

    items = []
    for a in alertas:
        if a["tipo"] == "vencimiento":
            referencia_id = a["lote"].id
            dias = a["dias"]
            url = f"/alertas/vence-pronto"
            if dias < 0:
                titulo = f"¡Lote vencido!"
            elif dias == 0:
                titulo = "¡Lote vence hoy!"
            elif dias <= alertas_service.umbrales_vencimiento()["critica"]:
                titulo = "Vence muy pronto"
            elif dias <= alertas_service.umbrales_vencimiento()["alta"]:
                titulo = "Vence pronto"
            else:
                titulo = "Próximo a vencer"
            mensaje = (
                f"{a['alimento'].nombre} · lote {a['lote'].codigo or a['lote'].id} "
                f"· vence en {dias} día(s)"
            )
            icono = "bi-calendar2-x"
        else:  # stock
            referencia_id = a["alimento"].id
            url = f"/monitoreo/stock"
            if a["nivel"] == "critica":
                titulo = "Sin stock"
            elif a["nivel"] == "alta":
                titulo = "Stock crítico bajo"
            else:
                titulo = "Stock bajo"
            mensaje = (
                f"{a['alimento'].nombre} · stock {a['stock']:g} de mínimo "
                f"{a['minimo']:g} {a['alimento'].unidad_medida}"
            )
            icono = "bi-exclamation-triangle"

        leida = _clave(a["tipo"], referencia_id) in read
        items.append(
            {
                "tipo": a["tipo"],
                "nivel": a["nivel"],
                "titulo": titulo,
                "mensaje": mensaje,
                "url": url,
                "icono": icono,
                "leida": leida,
            }
        )

    items.sort(
        key=lambda n: (
            n["leida"],
            PESO_NIVEL.get(n["nivel"], 3),
        )
    )
    no_leidas = sum(1 for n in items if not n["leida"])
    return {"items": items, "no_leidas": no_leidas, "total": len(items)}


def marcar_todas_como_leidas(usuario) -> int:
    """Marca todas las alertas actuales como leídas para el usuario.

    Devuelve el número de nuevas notificaciones marcadas.
    """
    nuevos = 0
    for a in alertas_service.todas():
        referencia_id = a["lote"].id if a["tipo"] == "vencimiento" else a["alimento"].id
        clave = _clave(a["tipo"], referencia_id)
        existe = (
            NotificacionLeida.query.filter_by(
                usuario_id=usuario.id, tipo=clave[0], referencia_id=clave[1]
            ).first()
            is not None
        )
        if not existe:
            db.session.add(
                NotificacionLeida(
                    usuario_id=usuario.id, tipo=clave[0], referencia_id=clave[1]
                )
            )
            nuevos += 1
    db.session.commit()
    return nuevos
