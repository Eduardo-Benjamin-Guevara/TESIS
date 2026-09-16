"""Entry point de la aplicación Flask para Vercel.

Vercel detecta automáticamente una instancia WSGI llamada `app` en archivos
reconocidos (app.py, index.py, main.py, wsgi.py, etc.) dentro de `api/` y
despliega la app como una Vercel Function (Fluid compute) sin configuración.
"""
import os
import sys

# Asegurar que la raíz del proyecto esté en sys.path
_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _RAIZ not in sys.path:
    sys.path.insert(0, _RAIZ)

from run import app