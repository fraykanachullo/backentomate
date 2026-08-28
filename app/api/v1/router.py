from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, diagnostic, plots, health

api_router = APIRouter(prefix="/api/v1")

# Endpoints con prefijo /api/v1
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(plots.router, prefix="/plots", tags=["plots"])
api_router.include_router(diagnostic.router, prefix="/diagnostic", tags=["diagnostic"])
