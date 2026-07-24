"""Punto de entrada WSGI para PythonAnywhere.

PythonAnywhere (plan gratuito incluido) sirve apps via WSGI.
FastAPI es ASGI, asi que lo adaptamos con a2wsgi.
"""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

PROJECT_HOME = Path(__file__).resolve().parent

if str(PROJECT_HOME) not in sys.path:
    sys.path.insert(0, str(PROJECT_HOME))

# Cargar .env ANTES de importar la app (pydantic-settings cachea Settings).
load_dotenv(PROJECT_HOME / ".env")

from a2wsgi import ASGIMiddleware  # noqa: E402
from app.main import app  # noqa: E402

application = ASGIMiddleware(app)
