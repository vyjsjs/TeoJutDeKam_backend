from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.security import get_current_user, get_current_user_optional
from app.schemas.ranking import (
    RankingResponse,
    GlobalRankingResponse,
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
def store_ranking(
    store_id: int,
    limit: int = Query(10, ge=1, le=50),
):
    """특정 매장의 터줏대감 순위 조회"""
    try:
        return get_store_ranking(store_id, limit)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/global", response_model=GlobalRankingResponse)
def global_ranking(
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user_optional),
):
    """전체 유저 포인트 순위 조회"""
    user_id = current_user["id"] if current_user else None
    return get_global_ranking(user_id, limit)


@router.get("/my/stores", response_model=MyStoreStatsResponse)
def my_store_stats(current_user: dict = Depends(get_current_user)):
    """내가 터줏대감인 매장 목록 (마이페이지)"""
    stats = get_user_store_stats(current_user["id"])
    return MyStoreStatsResponse(stores=stats, total=len(stats))


@router.get("/my/points", response_model=PointHistoryListResponse)
def my_point_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    """내 포인트 내역 조회 (마이페이지)"""
    return get_user_point_history(current_user["id"], skip, limit)
