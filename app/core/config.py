from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # --- App ---
    app_name: str = "Tomate Disease Detection API"
    app_version: str = "2.0.0"
    environment: str = "development"  # development | production
    debug: bool = True

    # --- Server ---
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "info"

    # --- Database ---
    # Desarrollo local: SQLite (cero config, funciona con Laragon MySQL como alternativa)
    # Producción/Supabase: postgresql+asyncpg://postgres.xxx:password@aws-0-....pooler.supabase.com:6543/postgres
    database_url: str = "sqlite+aiosqlite:///./tomate.db"
    # Sync URL para Alembic / scripts
    database_url_sync: str = "sqlite:///./tomate.db"
    # Alternativa MySQL Laragon (si prefieres usar MySQL de Laragon):
    # database_url: str = "mysql+aiomysql://root:@localhost:3306/tomate_db"
    # database_url_sync: str = "mysql+pymysql://root:@localhost:3306/tomate_db"

    # --- Supabase ---
    supabase_url: str = "https://xyzabcdef.supabase.co"
    supabase_key: str = "your-supabase-anon-key"
    supabase_service_key: str = "your-supabase-service-key"
    supabase_bucket: str = "diagnostic-images"

    # --- JWT ---
    jwt_secret_key: str = "change-me-super-secret-key-min-32-chars"
    jwt_algorithm: str = "HS256"
    jwt_access_expire_hours: int = 8
    jwt_refresh_expire_days: int = 30

    # --- Model ---
    model_path: str = "app/models/best.pt"
    max_upload_size_mb: int = 5
    # Carpeta de imagenes (en el servidor: un disco persistente, p.ej. /data/uploads)
    upload_dir: str = "uploads"
    image_size: int = 640
    confidence_threshold: float = 0.30
    iou_threshold: float = 0.45

    # --- CORS ---
    cors_origins: str = "*"  # comma-separated in prod: "https://app.example.com,https://admin.example.com"

    @property
    def cors_origins_list(self) -> List[str]:
        if self.cors_origins == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    # --- Admin maestro (se crea al arrancar si no existe) ---
    admin_name: str = "Administrador"
    admin_email: str = "admin@tomate.com"
    admin_password: str = "cambiar_esta_clave"  # el valor real va en .env (ADMIN_PASSWORD)

    # --- Rate limiting ---
    rate_limit_login: str = "5/minute"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()
