from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.security import get_current_user
from app.schemas.review import ReviewCreateRequest, ReviewResponse, ReviewListResponse
from app.services.review_service import create_review, get_store_reviews, get_user_reviews

router = APIRouter(prefix="/api/reviews", tags=["리뷰"])


@router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def write_review(
    data: ReviewCreateRequest,
    current_user: dict = Depends(get_current_user),
):
    """리뷰 작성 (포인트 자동 지급)"""
    if data.rating < 1 or data.rating > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="평점은 1~5 사이여야 합니다.",
        )
    try:
        review = create_review(current_user["id"], data)
        return review
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/store/{store_id}", response_model=ReviewListResponse)
def store_reviews(
    store_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    """특정 매장의 리뷰 목록 조회"""
    return get_store_reviews(store_id, skip, limit)


@router.get("/my", response_model=ReviewListResponse)
def my_reviews(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    """내가 작성한 리뷰 목록 조회"""
    return get_user_reviews(current_user["id"], skip, limit)
