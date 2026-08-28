import os
from datetime import datetime
from pathlib import Path

from app.core.config import settings

# Intentar importar supabase, si no existe o creds placeholder, usar fallback local
try:
    from supabase import create_client
    _has_supabase = True
except:
    _has_supabase = False

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

def _is_configured() -> bool:
    return _has_supabase and settings.supabase_url != "https://xyzabcdef.supabase.co" and "placeholder" not in settings.supabase_key

def upload_image(user_id: str, diagnostic_id: str, image_bytes: bytes, filename: str = "image.jpg") -> tuple[str, str]:
    """
    Retorna (image_url, storage_path). Si Supabase no configurado, guarda local en uploads/.
    """
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    storage_path = f"{user_id}/{date_str}/{diagnostic_id}.jpg"

    if _is_configured():
        try:
            client = create_client(settings.supabase_url, settings.supabase_service_key)
            client.storage.from_(settings.supabase_bucket).upload(storage_path, image_bytes, {"content-type": "image/jpeg", "upsert": "true"})
            # URL firmada 1h
            res = client.storage.from_(settings.supabase_bucket).create_signed_url(storage_path, 3600)
            url = res.get("signedURL") or res.get("signedUrl") or f"{settings.supabase_url}/storage/v1/object/public/{settings.supabase_bucket}/{storage_path}"
            return url, storage_path
        except Exception as e:
            print(f"[storage] Supabase error, fallback local: {e}")

    # Fallback local
    local_path = UPLOAD_DIR / storage_path
    local_path.parent.mkdir(parents=True, exist_ok=True)
    local_path.write_bytes(image_bytes)
    # URL local accesible via /uploads (servir estático si se monta) o file path
    url = f"/uploads/{storage_path}"
    return url, storage_path

def get_signed_url(storage_path: str, ttl: int = 3600) -> str:
    if _is_configured():
        try:
            client = create_client(settings.supabase_url, settings.supabase_service_key)
            res = client.storage.from_(settings.supabase_bucket).create_signed_url(storage_path, ttl)
            return res.get("signedURL") or res.get("signedUrl") or ""
        except:
            pass
    return f"/uploads/{storage_path}"
