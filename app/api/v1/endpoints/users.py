from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional

from app.database.session import get_db
from app.api.deps import get_current_user, require_role
from app.models.orm.user import User
from app.core.security import hash_password

router = APIRouter()

class UserUpdateRequest(BaseModel):
    name: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

@router.get("/me")
async def get_me(payload: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == payload["user_id"]))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }

@router.get("")
async def list_users(payload: dict = Depends(require_role(["ADMIN"])), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    return [
        {"id": u.id, "name": u.name, "email": u.email, "role": u.role, "is_active": u.is_active, "created_at": u.created_at.isoformat() if u.created_at else None}
        for u in users
    ]

@router.patch("/{user_id}")
async def update_user(user_id: str, req: UserUpdateRequest, payload: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # Solo propietario o ADMIN
    if payload["user_id"] != user_id and payload["role"] != "ADMIN":
        raise HTTPException(status_code=403, detail="Permiso denegado")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if req.name is not None:
        user.name = req.name
    if req.password is not None:
        if len(req.password) < 8:
            raise HTTPException(status_code=422, detail="Contraseña muy corta")
        user.password_hash = hash_password(req.password)
    if req.role is not None:
        if payload["role"] != "ADMIN":
            raise HTTPException(status_code=403, detail="Solo ADMIN puede cambiar roles")
        if req.role not in ("ADMIN", "FIELD_TECH"):
            raise HTTPException(status_code=422, detail="Rol invalido")
        user.role = req.role
    if req.is_active is not None:
        if payload["role"] != "ADMIN":
            raise HTTPException(status_code=403, detail="Solo ADMIN puede activar/desactivar")
        user.is_active = req.is_active
        if not req.is_active:
            # Revocar tokens al desactivar
            from app.models.orm.refresh_token import RefreshToken
            from datetime import datetime, timezone
            r = await db.execute(select(RefreshToken).where(RefreshToken.user_id == user_id, RefreshToken.is_revoked == False))
            for t in r.scalars().all():
                t.is_revoked = True
                t.revoked_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(user)
    return {"id": user.id, "name": user.name, "email": user.email, "role": user.role, "is_active": user.is_active}
