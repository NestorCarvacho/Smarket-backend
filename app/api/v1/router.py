from fastapi import APIRouter

from app.api.v1 import auth, items, lists, purchases

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(lists.router, prefix="/lists", tags=["shopping-lists"])
api_router.include_router(items.router, prefix="/lists", tags=["list-items"])
api_router.include_router(purchases.router, prefix="/lists", tags=["purchases"])
