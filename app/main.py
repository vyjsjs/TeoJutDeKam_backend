from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

# Import routers
from app.routers import auth, stores, visits, reviews, ranking, mypage


app = FastAPI(
    title="터줏대감 API",
    description="위치 기반 매장 방문 인증 & 점령 순위 서비스",
    version="1.0.0",
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
def root():
    return {
        "service": "터줏대감 API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "ok"}
