"""Utilidades de fecha/hora.

Centraliza la obtención de la hora UTC para evitar el uso de la API
deprecada `datetime.utcnow()` y mantener consistencia (naive UTC),
compatible con SQLite.
"""
from datetime import datetime, timezone


def utcnow() -> datetime:
    """Devuelve la fecha/hora actual en UTC (sin zona horaria).

    Se devuelve naive UTC para ser plenamente compatible con las columnas
    `DateTime` de SQLite y con la comparación de fechas de la app.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)
