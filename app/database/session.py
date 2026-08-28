from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

# SQLite necesita check_same_thread=False via connect_args, pero async engine lo maneja solo
connect_args = {}
if "sqlite" in settings.database_url:
    connect_args = {"check_same_thread": False}

engine = create_async_engine(
    settings.database_url,
    echo=False,
    connect_args=connect_args,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    """Crea tablas si no existen (dev). En producción usar Alembic."""
    from app.models.orm.base import Base
    # Importar modelos para que se registren en metadata
    import app.models.orm.user  # noqa
    import app.models.orm.refresh_token  # noqa
    import app.models.orm.plot  # noqa
    import app.models.orm.diagnostic  # noqa
    import app.models.orm.audit_log  # noqa
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
