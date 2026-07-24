"""Punto de entrada WSGI para PythonAnywhere (uWSGI).

FastAPI es ASGI; lo adaptamos con a2wsgi. Incluye un /health sincrono
para diagnosticar si el hang viene del adaptador ASGI.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_HOME = Path("/home/nestorcarvacho/Smarket-backend")

# uWSGI a veces arranca en /home/usuario; forzar cwd del proyecto.
os.chdir(PROJECT_HOME)
if str(PROJECT_HOME) not in sys.path:
    sys.path.insert(0, str(PROJECT_HOME))

from dotenv import load_dotenv

load_dotenv(PROJECT_HOME / ".env")

# Si Settings se cacheo antes, limpiar.
try:
    from app.core.config import get_settings

    get_settings.cache_clear()
except Exception:
    pass

from a2wsgi import ASGIMiddleware
from app.main import app as fastapi_app

_asgi_application = ASGIMiddleware(fastapi_app)


def application(environ, start_response):
    """WSGI callable con bypass sincrono de /health."""
    path = environ.get("PATH_INFO", "")
    if path == "/health" or path == "/health/":
        body = b'{"status":"ok"}'
        start_response(
            "200 OK",
            [
                ("Content-Type", "application/json"),
                ("Content-Length", str(len(body))),
            ],
        )
        return [body]
    return _asgi_application(environ, start_response)
