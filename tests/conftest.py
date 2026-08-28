import sys
sys.path.insert(0, r'D:\AppTomateDetecion\tomate_backend')

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from httpx import AsyncClient, ASGITransport

from app.models.orm.base import Base
import app.models.orm.user
import app.models.orm.refresh_token
import app.models.orm.plot
import app.models.orm.diagnostic
import app.models.orm.audit_log
from app.database.session import get_db
from app.main import app

TEST_DB_URL = "sqlite+aiosqlite:///./test.db"

@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(test_engine):
    Session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as session:
        yield session
        await session.rollback()

@pytest_asyncio.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()

@pytest_asyncio.fixture
async def admin_token(client, db_session):
    # Intenta login primero (si ya existe de test previo)
    r = await client.post("/api/v1/auth/login", json={"email": "testadmin@upeu.edu.pe", "password": "Admin1234"})
    if r.status_code == 200:
        return r.json()["access_token"]
    # Si no existe, crear directamente en DB (bypass 403 bootstrap)
    from app.models.orm.user import User
    from app.core.security import hash_password
    from sqlalchemy import select
    res = await db_session.execute(select(User).where(User.email == "testadmin@upeu.edu.pe"))
    if not res.scalars().first():
        u = User(name="Test Admin", email="testadmin@upeu.edu.pe", password_hash=hash_password("Admin1234"), role="ADMIN")
        db_session.add(u)
        await db_session.commit()
    r = await client.post("/api/v1/auth/login", json={"email": "testadmin@upeu.edu.pe", "password": "Admin1234"})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]

@pytest_asyncio.fixture
async def user_token(client, db_session):
    r = await client.post("/api/v1/auth/login", json={"email": "testtech@upeu.edu.pe", "password": "Tech1234"})
    if r.status_code == 200:
        return r.json()["access_token"]
    # Crear si no existe
    await client.post("/api/v1/auth/register", json={"name": "Test Tech", "email": "testtech@upeu.edu.pe", "password": "Tech1234", "role": "FIELD_TECH"})
    r = await client.post("/api/v1/auth/login", json={"email": "testtech@upeu.edu.pe", "password": "Tech1234"})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]

@pytest_asyncio.fixture
async def plot_id(client, admin_token):
    r = await client.post("/api/v1/plots", json={"name": "Lote Test", "latitude": -16.3, "longitude": -72.2}, headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 201, r.text
    return r.json()["id"]
