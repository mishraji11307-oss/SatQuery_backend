"""
SatQuery AI - Pytest Test Configuration & Fixtures
"""
import sys
import os
import shutil
from pathlib import Path
from typing import AsyncGenerator
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from PIL import Image, ImageDraw

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set test environment
os.environ["APP_ENV"] = "test"
os.environ["DEMO_MODE"] = "true"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["UPLOAD_DIR"] = "./storage/test_uploads"
os.environ["EVIDENCE_DIR"] = "./storage/test_evidence"

from app.main import app
from app.db.database import Base, get_db
from app.core.config import settings

# Test async database engine
test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
)
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


@pytest.fixture(scope="session", autouse=True)
def setup_test_directories():
    os.makedirs("./storage/test_uploads", exist_ok=True)
    os.makedirs("./storage/test_evidence", exist_ok=True)
    yield
    shutil.rmtree("./storage/test_uploads", ignore_errors=True)
    shutil.rmtree("./storage/test_evidence", ignore_errors=True)


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with test_engine.begin() as conn:
        from app.db import models  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session
        await session.rollback()

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def sample_optical_image(tmp_path) -> str:
    img_path = tmp_path / "test_optical.png"
    img = Image.new("RGB", (256, 256), color=(60, 100, 60))
    d = ImageDraw.Draw(img)
    d.rectangle([50, 50, 150, 150], fill=(200, 200, 200))
    img.save(str(img_path))
    return str(img_path)


@pytest.fixture
def sample_sar_image(tmp_path) -> str:
    img_path = tmp_path / "test_sar.png"
    img = Image.new("L", (256, 256), color=128)
    d = ImageDraw.Draw(img)
    d.rectangle([50, 50, 150, 150], fill=255)
    img.save(str(img_path))
    return str(img_path)
