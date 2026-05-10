from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine, Base

# Import all models so they are registered with Base.metadata
from app.models.user import User  # noqa: F401
from app.models.store import Store  # noqa: F401
from app.models.visit_certification import VisitCertification  # noqa: F401
from app.models.store_user_stats import StoreUserStats  # noqa: F401
from app.models.review import Review  # noqa: F401
from app.models.point_history import PointHistory  # noqa: F401

# Import routers
from app.routers import auth, stores, visits, reviews, ranking, mypage


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables if they don't exist (dev convenience)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(
    title="터줏대감 API",
    description="위치 기반 매장 방문 인증 & 점령 순위 서비스",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(stores.router)
app.include_router(visits.router)
app.include_router(reviews.router)
app.include_router(ranking.router)
app.include_router(mypage.router)


@app.get("/")
async def root():
    return {
        "service": "터줏대감 API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
