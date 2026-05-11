from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.database import supabase
from app.core.security import get_current_user_optional
from app.schemas.store import (
    StoreResponse,
    StoreListResponse,
    StoreDetailResponse,
    StoreCreateRequest,
)
from app.services.visit_service import haversine_distance

router = APIRouter(prefix="/api/stores", tags=["매장"])


@router.get("", response_model=StoreListResponse)
def list_stores(
    category: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """매장 목록 조회 (카테고리, 검색어 필터링)"""
    query = supabase.table("stores").select("*", count="exact")

    if category:
        query = query.eq("category", category)
    if search:
        query = query.ilike("name", f"%{search}%")

    result = query.range(skip, skip + limit - 1).execute()
    total = result.count or 0

    return StoreListResponse(
        stores=[StoreResponse(**s) for s in result.data],
        total=total,
    )


@router.get("/nearby", response_model=StoreListResponse)
def nearby_stores(
    latitude: float = Query(..., description="사용자 위도"),
    longitude: float = Query(..., description="사용자 경도"),
    radius: int = Query(1000, description="검색 반경(미터)"),
):
    """위치 기반 근처 매장 검색"""
    result = supabase.table("stores").select("*").execute()

    nearby = []
    for store in result.data:
        dist = haversine_distance(
            latitude, longitude,
            float(store["latitude"]), float(store["longitude"]),
        )
        if dist <= radius:
            nearby.append(StoreResponse(**store))

    return StoreListResponse(stores=nearby, total=len(nearby))


@router.get("/{store_id}", response_model=StoreDetailResponse)
def get_store_detail(store_id: int):
    """매장 상세 조회 (방문 수, 리뷰 수, 평점 포함)"""
    result = supabase.table("stores").select("*").eq("id", store_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="매장을 찾을 수 없습니다.")
    store = result.data[0]

    # Total visits
    visit_result = supabase.table("visit_certifications") \
        .select("id", count="exact") \
        .eq("store_id", store_id) \
        .eq("status", "approved") \
        .execute()
    total_visits = visit_result.count or 0

    # Total reviews & average rating
    review_result = supabase.table("reviews") \
        .select("rating", count="exact") \
        .eq("store_id", store_id) \
        .execute()
    total_reviews = review_result.count or 0

    avg_rating = None
    if review_result.data:
        ratings = [r["rating"] for r in review_result.data]
        avg_rating = round(sum(ratings) / len(ratings), 1)

    return StoreDetailResponse(
        **store,
        total_visits=total_visits,
        total_reviews=total_reviews,
        average_rating=avg_rating,
    )


@router.post("", response_model=StoreResponse, status_code=status.HTTP_201_CREATED)
def create_store(data: StoreCreateRequest):
    """매장 등록 (관리자용)"""
    store_data = data.model_dump(exclude_none=True)
    result = supabase.table("stores").insert(store_data).execute()
    return StoreResponse(**result.data[0])
