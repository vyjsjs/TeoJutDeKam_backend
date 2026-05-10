from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.review import ReviewCreateRequest, ReviewResponse, ReviewListResponse
from app.services.review_service import create_review, get_store_reviews, get_user_reviews

router = APIRouter(prefix="/api/reviews", tags=["리뷰"])


@router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def write_review(
    data: ReviewCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """리뷰 작성 (포인트 자동 지급)"""
    if data.rating < 1 or data.rating > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="평점은 1~5 사이여야 합니다.",
        )
    try:
        review = await create_review(db, current_user.id, data)
        return review
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/store/{store_id}", response_model=ReviewListResponse)
async def store_reviews(
    store_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """특정 매장의 리뷰 목록 조회"""
    return await get_store_reviews(db, store_id, skip, limit)


@router.get("/my", response_model=ReviewListResponse)
async def my_reviews(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """내가 작성한 리뷰 목록 조회"""
    return await get_user_reviews(db, current_user.id, skip, limit)
