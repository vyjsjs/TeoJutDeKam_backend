from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, get_current_user_optional
from app.models.user import User
from app.schemas.ranking import (
    RankingResponse,
    GlobalRankingResponse,
    StoreUserStatsResponse,
    PointHistoryListResponse,
    MyStoreStatsResponse,
)
from app.services.ranking_service import (
    get_store_ranking,
    get_global_ranking,
    get_user_store_stats,
    get_user_point_history,
)

router = APIRouter(prefix="/api/ranking", tags=["순위/포인트"])


@router.get("/store/{store_id}", response_model=RankingResponse)
async def store_ranking(
    store_id: int,
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """특정 매장의 터줏대감 순위 조회"""
    try:
        return await get_store_ranking(db, store_id, limit)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/global", response_model=GlobalRankingResponse)
async def global_ranking(
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """전체 유저 포인트 순위 조회"""
    user_id = current_user.id if current_user else None
    return await get_global_ranking(db, user_id, limit)


@router.get("/my/stores", response_model=MyStoreStatsResponse)
async def my_store_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """내가 터줏대감인 매장 목록 (마이페이지)"""
    stats = await get_user_store_stats(db, current_user.id)
    return MyStoreStatsResponse(stores=stats, total=len(stats))


@router.get("/my/points", response_model=PointHistoryListResponse)
async def my_point_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """내 포인트 내역 조회 (마이페이지)"""
    return await get_user_point_history(db, current_user.id, skip, limit)
