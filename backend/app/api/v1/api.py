from fastapi import APIRouter

from app.api.v1.endpoints import admin, auth, automation, conversations, health, notifications, users

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(automation.router, prefix="/automation", tags=["automation"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])

