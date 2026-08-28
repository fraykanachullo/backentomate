from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import verify_token

security = HTTPBearer(auto_error=False)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No autenticado")
    token = credentials.credentials
    try:
        payload = verify_token(token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalido o expirado")
    return payload  # dict con user_id, role, exp, jti


def require_role(allowed_roles: list[str]):
    async def checker(payload: dict = Depends(get_current_user)):
        role = payload.get("role")
        if role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permiso denegado")
        return payload
    return checker
