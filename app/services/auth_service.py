from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.models.orm.user import User
from app.models.orm.refresh_token import RefreshToken
from app.models.orm.audit_log import AuditLog
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, hash_refresh_token
from app.core.config import settings


def _now_utc():
    return datetime.now(timezone.utc)

def _ensure_aware(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


async def _log_audit(db: AsyncSession, user_id: str | None, action: str, ip: str | None = None, ua: str | None = None, details: dict | None = None):
    log = AuditLog(user_id=user_id, action=action, ip_address=ip, user_agent=ua, details=details)
    db.add(log)


async def register_user(db: AsyncSession, name: str, email: str, password: str, role: str = "FIELD_TECH", requester_role: str | None = None):
    # Role check: solo ADMIN puede crear ADMIN
    if role == "ADMIN" and requester_role != "ADMIN":
        # Permitir primer usuario ADMIN si no hay usuarios (bootstrap)
        result = await db.execute(select(User).limit(1))
        if result.scalars().first() is not None:
            raise HTTPException(status_code=403, detail="Solo un administrador puede crear administradores")

    # Validaciones
    if len(password) < 8:
        raise HTTPException(status_code=422, detail="La contraseña debe tener mínimo 8 caracteres")
    if role not in ("ADMIN", "FIELD_TECH"):
        raise HTTPException(status_code=422, detail="Rol inválido")

    existing = await db.execute(select(User).where(User.email == email.lower()))
    if existing.scalars().first():
        raise HTTPException(status_code=409, detail="El correo ya está registrado")

    user = User(
        name=name,
        email=email.lower(),
        password_hash=hash_password(password),
        role=role,
    )
    db.add(user)
    await db.flush()
    await _log_audit(db, user.id, "USER_REGISTER", details={"email": email, "role": role})
    await db.commit()
    await db.refresh(user)
    return user


async def login_user(db: AsyncSession, email: str, password: str, ip: str | None = None, ua: str | None = None):
    result = await db.execute(select(User).where(User.email == email.lower()))
    user = result.scalars().first()

    # Mensaje genérico por seguridad
    invalid_exc = HTTPException(status_code=401, detail="Credenciales inválidas")

    if not user:
        raise invalid_exc

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Cuenta deshabilitada")

    # Verificar bloqueo
    locked_until = _ensure_aware(user.locked_until)
    if locked_until and locked_until > _now_utc():
        remaining = int((locked_until - _now_utc()).total_seconds())
        raise HTTPException(status_code=423, detail={"code": "ACCOUNT_LOCKED", "message": "Cuenta bloqueada temporalmente", "retry_after": remaining})

    if not verify_password(password, user.password_hash):
        user.failed_attempts = (user.failed_attempts or 0) + 1
        if user.failed_attempts >= 5:
            user.locked_until = _now_utc() + timedelta(minutes=10)
            await _log_audit(db, user.id, "LOGIN_FAILED_LOCKED", ip, ua, {"failed_attempts": user.failed_attempts})
        else:
            await _log_audit(db, user.id, "LOGIN_FAILED", ip, ua, {"failed_attempts": user.failed_attempts})
        await db.commit()
        # Si se acaba de bloquear
        locked_until = _ensure_aware(user.locked_until)
        if locked_until and locked_until > _now_utc():
            remaining = int((locked_until - _now_utc()).total_seconds())
            raise HTTPException(status_code=423, detail={"code": "ACCOUNT_LOCKED", "message": "Cuenta bloqueada temporalmente", "retry_after": remaining})
        raise invalid_exc

    # Éxito: reset contadores
    user.failed_attempts = 0
    user.locked_until = None
    user.last_login_at = _now_utc()

    # Crear tokens
    access_token = create_access_token(user.id, user.role)
    raw_refresh = create_refresh_token()
    token_hash = hash_refresh_token(raw_refresh)
    expires_at = _now_utc() + timedelta(days=settings.jwt_refresh_expire_days)

    refresh = RefreshToken(user_id=user.id, token_hash=token_hash, expires_at=expires_at)
    db.add(refresh)
    await _log_audit(db, user.id, "LOGIN_SUCCESS", ip, ua)
    await db.commit()
    await db.refresh(user)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.jwt_access_expire_hours * 3600,
        "refresh_token": raw_refresh,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        },
    }


async def refresh_access_token(db: AsyncSession, refresh_token_raw: str):
    token_hash = hash_refresh_token(refresh_token_raw)
    result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    rt = result.scalars().first()
    expires_at = _ensure_aware(rt.expires_at) if rt else None
    if not rt or rt.is_revoked or (expires_at and expires_at < _now_utc()):
        raise HTTPException(status_code=401, detail="Refresh token inválido o expirado")

    # Buscar usuario
    result = await db.execute(select(User).where(User.id == rt.user_id))
    user = result.scalars().first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Usuario no válido")

    new_access = create_access_token(user.id, user.role)
    return {
        "access_token": new_access,
        "token_type": "bearer",
        "expires_in": settings.jwt_access_expire_hours * 3600,
    }


async def logout_user(db: AsyncSession, user_id: str):
    # Revocar todos los refresh tokens del usuario
    result = await db.execute(select(RefreshToken).where(RefreshToken.user_id == user_id, RefreshToken.is_revoked == False))
    tokens = result.scalars().all()
    for t in tokens:
        t.is_revoked = True
        t.revoked_at = _now_utc()
    await _log_audit(db, user_id, "LOGOUT")
    await db.commit()
    return {"message": "Sesión cerrada"}
