from fastapi import APIRouter

from app.api.v1 import admin, ask, auth, bookmarks, content, learning, sources, users

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(bookmarks.router)
api_router.include_router(admin.router)
api_router.include_router(sources.public_router)
api_router.include_router(sources.admin_router)
api_router.include_router(content.router)
api_router.include_router(ask.router)
api_router.include_router(learning.router)
api_router.include_router(learning.admin_router)
