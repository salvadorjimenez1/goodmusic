import sys
from pathlib import Path

import asyncio
from collections.abc import AsyncIterator, Iterator
import importlib

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

API_APP_PATH = PROJECT_ROOT / "apps" / "api"
if str(API_APP_PATH) not in sys.path:
    sys.path.insert(0, str(API_APP_PATH))

db = importlib.import_module("db")
main_module = importlib.import_module("main")
Base = db.Base
get_db = db.get_db
app = main_module.app
app_engine = main_module.engine


@pytest.fixture(scope="session")
def event_loop() -> Iterator[asyncio.AbstractEventLoop]:
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine() -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    original_engine = db.engine
    original_sessionmaker = db.AsyncSessionLocal
    original_app_engine = app_engine

    test_sessionmaker = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    db.engine = engine
    db.AsyncSessionLocal = test_sessionmaker
    main_module.engine = engine

    try:
        yield engine
    finally:
        db.engine = original_engine
        db.AsyncSessionLocal = original_sessionmaker
        main_module.engine = original_app_engine
        await engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def reset_database(test_engine: AsyncEngine) -> AsyncIterator[None]:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest_asyncio.fixture
async def session(reset_database: None) -> AsyncIterator[AsyncSession]:
    async with db.AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.rollback()


@pytest_asyncio.fixture(autouse=True)
async def override_get_db(session: AsyncSession) -> AsyncIterator[None]:
    async def _get_db() -> AsyncIterator[AsyncSession]:
        yield session

    app.dependency_overrides[get_db] = _get_db
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=transport, base_url="http://test") as async_client:
            yield async_client
