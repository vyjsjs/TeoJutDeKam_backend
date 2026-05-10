from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.security import get_current_user_optional
from app.models.store import Store
from app.models.review import Review
from app.models.visit_certification import VisitCertification
from app.schemas.store import (
    StoreResponse,
    StoreListResponse,
    StoreDetailResponse,
    StoreCreateRequest,
    NearbyStoreRequest,
)
from app.services.visit_service import haversine_distance

router = APIRouter(prefix="/api/stores", tags=["매장"])


@router.get("", response_model=StoreListResponse)
async def list_stores(
    category: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """매장 목록 조회 (카테고리, 검색어 필터링)"""
    query = select(Store)

    if category:
        query = query.where(Store.category == category)
    if search:
        query = query.where(Store.name.ilike(f"%{search}%"))

    # Count
    count_query = select(func.count(Store.id))
    if category:
        count_query = count_query.where(Store.category == category)
    if search:
        count_query = count_query.where(Store.name.ilike(f"%{search}%"))

    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    result = await db.execute(query.offset(skip).limit(limit))
    stores = result.scalars().all()

    return StoreListResponse(
        stores=[StoreResponse.model_validate(s) for s in stores],
        total=total,
    )


@router.get("/nearby", response_model=StoreListResponse)
async def nearby_stores(
    latitude: float = Query(..., description="사용자 위도"),
    longitude: float = Query(..., description="사용자 경도"),
    radius: int = Query(1000, description="검색 반경(미터)"),
    db: AsyncSession = Depends(get_db),
):
    """위치 기반 근처 매장 검색"""
    result = await db.execute(select(Store))
    all_stores = result.scalars().all()

    nearby = []
    for store in all_stores:
        dist = haversine_distance(
            latitude, longitude,
            float(store.latitude), float(store.longitude),
        )
        if dist <= radius:
            nearby.append(store)

    return StoreListResponse(
        stores=[StoreResponse.model_validate(s) for s in nearby],
        total=len(nearby),
    )


@router.get("/{store_id}", response_model=StoreDetailResponse)
async def get_store_detail(
    store_id: int,
    db: AsyncSession = Depends(get_db),
):
    """매장 상세 조회 (방문 수, 리뷰 수, 평점 포함)"""
    result = await db.execute(select(Store).where(Store.id == store_id))
    store = result.scalar_one_or_none()
    if not store:
        raise HTTPException(status_code=404, detail="매장을 찾을 수 없습니다.")

    # Total visits
    visit_count = await db.execute(
        select(func.count(VisitCertification.id)).where(
            VisitCertification.store_id == store_id,
            VisitCertification.status == "approved",
        )
    )
    total_visits = visit_count.scalar() or 0

    # Total reviews
    review_count = await db.execute(
        select(func.count(Review.id)).where(Review.store_id == store_id)
    )
    total_reviews = review_count.scalar() or 0

    # Average rating
    avg_result = await db.execute(
        select(func.avg(Review.rating)).where(Review.store_id == store_id)
    )
    avg_rating = avg_result.scalar()

    return StoreDetailResponse(
        id=store.id,
        name=store.name,
        category=store.category,
        address=store.address,
        latitude=float(store.latitude),
        longitude=float(store.longitude),
        phone=store.phone,
        image_url=store.image_url,
        created_at=store.created_at,
        total_visits=total_visits,
        total_reviews=total_reviews,
        average_rating=round(float(avg_rating), 1) if avg_rating else None,
    )


@router.post("", response_model=StoreResponse, status_code=status.HTTP_201_CREATED)
async def create_store(
    data: StoreCreateRequest,
    db: AsyncSession = Depends(get_db),
):
    """매장 등록 (관리자용)"""
    store = Store(
        name=data.name,
        category=data.category,
        address=data.address,
        latitude=data.latitude,
        longitude=data.longitude,
        phone=data.phone,
        image_url=data.image_url,
    )
    db.add(store)
    await db.flush()
    await db.refresh(store)
    return StoreResponse.model_validate(store)
