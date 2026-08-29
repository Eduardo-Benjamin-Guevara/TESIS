"""Servicio de códigos QR para alimentos.

Genera un código QR (PNG en memoria) con la información clave del alimento,
útil para identificación rápida y trazabilidad (impresión y escaneo).
"""
import io

import qrcode


def generar_qr(alimento, datos_extra: dict | None = None) -> bytes:
    """Genera el PNG del código QR con los datos del alimento."""
    aparato = {
        "app": "Sistema de Alimentos I.E.I. 1488",
        "codigo": alimento.codigo,
        "nombre": alimento.nombre,
        "stock": f"{float(alimento.stock_actual or 0):.2f}",
        "unidad": alimento.unidad_medida,
    }
    if datos_extra:
        aparato.update(datos_extra)

    contenido = "\n".join(f"{k}: {v}" for k, v in aparato.items())

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(contenido)
    qr.make(fit=True)

    imagen = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    imagen.save(buffer, format="PNG")
    return buffer.getvalue()