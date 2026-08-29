"""Funciones auxiliares de seguridad variadas."""
import os
import secrets


def generar_secret_key() -> str:
    """Genera una clave secreta segura de 32 bytes."""
    return secrets.token_hex(32)


def obtener_var_entorno(nombre: str, defecto: str = "") -> str:
    """Lee una variable de entorno con un valor por defecto."""
    return os.environ.get(nombre, defecto)
