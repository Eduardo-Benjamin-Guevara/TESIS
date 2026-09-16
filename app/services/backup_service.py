"""Servicio de copias de seguridad de la base de datos.

Genera copias de seguridad de la base de datos SQLite (archivos `.db.bak`)
en la carpeta `backups/` del proyecto, y permite listarlas. Es compatible con
estrategias de respaldo programadas (cron) y con restauración manual
(copiar el archivo de vuelta al nombre original).
"""
import os
import shutil
from datetime import datetime

from app.extensions import db

DIRECTORIO_BACKUPS = os.path.join(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")),
    "backups",
)


def _ruta_bd_actual() -> str:
    """Devuelve la ruta del archivo SQLite que usa la aplicación."""
    uri = db.engine.url.database
    if not uri:
        raise RuntimeError("No se pudo determinar la ruta de la base de datos.")
    return uri


def crear_backup(destino: str | None = None) -> str:
    """Crea una copia de seguridad de la base de datos.

    Si `destino` es None, guarda en `backups/sistema_alimentos_AAAAMMDD_HHMMSS.db`.
    Devuelve la ruta absoluta del archivo creado.
    """
    # Expurgar cualquier transacción pendiente antes de copiar
    db.session.remove()

    origen = _ruta_bd_actual()
    if not os.path.exists(origen):
        raise RuntimeError(
            f"No se encontró la base de datos en {origen}. "
            "Ejecuta primero las migraciones (flask --app run.py db upgrade)."
        )

    if destino:
        os.makedirs(os.path.dirname(os.path.abspath(destino)), exist_ok=True)
        ruta_final = destino
    else:
        os.makedirs(DIRECTORIO_BACKUPS, exist_ok=True)
        nombre = f"sistema_alimentos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        ruta_final = os.path.join(DIRECTORIO_BACKUPS, nombre)

    with open(origen, "rb") as f_in, open(ruta_final, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)
    return ruta_final


def listar_backups() -> list[dict]:
    """Lista las copias de seguridad en la carpeta `backups/`, más reciente primero."""
    if not os.path.isdir(DIRECTORIO_BACKUPS):
        return []
    items = []
    for nombre in sorted(os.listdir(DIRECTORIO_BACKUPS), reverse=True):
        ruta = os.path.join(DIRECTORIO_BACKUPS, nombre)
        if os.path.isfile(ruta) and nombre.endswith(".db"):
            stat = os.stat(ruta)
            items.append({
                "archivo": nombre,
                "fecha": datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y %H:%M"),
                "tamano": f"{stat.st_size / 1024:.1f} KB",
            })
    return items