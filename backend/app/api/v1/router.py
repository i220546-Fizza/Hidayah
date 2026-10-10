from fastapi import APIRouter

from app.api.v1 import admin, auth, bookmarks, users

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(bookmarks.router)
api_router.include_router(admin.router)
