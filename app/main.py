from contextlib import asynccontextmanager
from html import escape

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

from app.api.deps import get_shopping_list_service
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import (
    AccountLockedError,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
)
from app.db.base import Base
from app.db.migrate import ensure_schema
from app.db.session import engine
from app.models import ListItem, ListMember, Purchase, ShoppingList, User  # noqa: F401
from app.services.shopping_list_service import ShoppingListService


@asynccontextmanager
async def lifespan(_app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await ensure_schema(conn)
    yield


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(ConflictError)
async def conflict_handler(request: Request, exc: ConflictError) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(UnauthorizedError)
async def unauthorized_handler(request: Request, exc: UnauthorizedError) -> JSONResponse:
    return JSONResponse(status_code=401, content={"detail": str(exc)})


@app.exception_handler(ForbiddenError)
async def forbidden_handler(request: Request, exc: ForbiddenError) -> JSONResponse:
    return JSONResponse(status_code=403, content={"detail": str(exc)})


@app.exception_handler(AccountLockedError)
async def account_locked_handler(request: Request, exc: AccountLockedError) -> JSONResponse:
    return JSONResponse(status_code=403, content={"detail": str(exc), "code": "account_locked"})


app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/join/{share_token}", response_class=HTMLResponse, tags=["join"])
async def join_landing(
    share_token: str,
    service: ShoppingListService = Depends(get_shopping_list_service),
) -> HTMLResponse:
    """Pagina HTTPS para WhatsApp: abre la app o muestra el codigo para unirse."""
    try:
        shopping_list = await service.get_invite_preview(share_token)
        list_name = escape(shopping_list.name)
        item_count = len(shopping_list.items or [])
        valid = True
    except NotFoundError:
        list_name = "Invitacion invalida"
        item_count = 0
        valid = False

    token = escape(share_token)
    deep_link = f"smarket://join/{token}"
    # Intent nativo Android (mejor que custom scheme desde Chrome/WhatsApp WebView)
    intent_link = (
        f"intent://join/{token}#Intent;scheme=smarket;package=com.nestorcarvacho.smarket;end"
    )

    body = f"""
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Smarket · Unirse a lista</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif; background:#0b0b0f; color:#fff; margin:0; padding:24px; }}
    .card {{ max-width:420px; margin:40px auto; background:#17171c; border-radius:20px; padding:28px; }}
    h1 {{ font-size:28px; margin:0 0 8px; }}
    p {{ color:#b8b8c0; line-height:1.45; }}
    .code {{ font-size:22px; letter-spacing:1px; background:#22222a; padding:14px; border-radius:12px; word-break:break-all; user-select:all; }}
    a.btn {{ display:block; text-align:center; margin-top:18px; background:#007AFF; color:#fff; text-decoration:none; padding:14px 16px; border-radius:14px; font-weight:700; }}
    a.secondary {{ display:block; text-align:center; margin-top:12px; color:#8ec5ff; }}
  </style>
</head>
<body>
  <div class="card">
    <h1>Smarket</h1>
    {"<p>Te invitaron a la lista <strong>" + list_name + "</strong> (" + str(item_count) + " productos).</p>" if valid else "<p>Este link de invitacion no es valido o expiro.</p>"}
    {"<p>Toca <strong>Abrir en Smarket</strong>. Si no abre, copia el codigo y en la app usa Mis listas → icono de link.</p>" if valid else ""}
    {"<div class='code' id='code'>" + token + "</div>" if valid else ""}
    {"<a class='btn' id='openBtn' href='" + intent_link + "'>Abrir en Smarket</a>" if valid else ""}
    {"<a class='secondary' href='" + deep_link + "'>Probar link directo</a>" if valid else ""}
  </div>
  <script>
    {"(function(){ var ua=navigator.userAgent||''; var android=/Android/i.test(ua); var intent='" + intent_link + "'; var deep='" + deep_link + "'; var btn=document.getElementById('openBtn'); if(btn){ btn.href = android ? intent : deep; } var target = android ? intent : deep; setTimeout(function(){ window.location.href = target; }, 300); })();" if valid else ""}
  </script>
</body>
</html>
"""
    return HTMLResponse(content=body)
