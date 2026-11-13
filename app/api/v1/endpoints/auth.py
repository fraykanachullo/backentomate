from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr, Field

from app.database.session import get_db
from app.services import auth_service
from app.api.deps import get_current_user

router = APIRouter()

class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    role: str = Field(default="FIELD_TECH", pattern="^(ADMIN|FIELD_TECH)$")

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)

class RefreshRequest(BaseModel):
    refresh_token: str

@router.post("/register", status_code=201)
async def register(req: RegisterRequest, request: Request, db: AsyncSession = Depends(get_db), current=Depends(lambda: None)):
    # Intentar obtener rol del solicitante si hay token (opcional)
    requester_role = None
    auth = request.headers.get("authorization")
    if auth and auth.lower().startswith("bearer "):
        try:
            from app.core.security import verify_token
            payload = verify_token(auth.split(" ", 1)[1])
            requester_role = payload.get("role")
        except:
            pass
    user = await auth_service.register_user(db, req.name, req.email, req.password, req.role, requester_role)
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }

@router.post("/login")
async def login(req: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    return await auth_service.login_user(db, req.email, req.password, ip, ua)

@router.post("/refresh")
async def refresh(req: RefreshRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.refresh_access_token(db, req.refresh_token)

@router.post("/logout")
async def logout(db: AsyncSession = Depends(get_db), payload: dict = Depends(get_current_user)):
    return await auth_service.logout_user(db, payload["user_id"])
