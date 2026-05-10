from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.review import Review
from app.models.user import User
from app.models.store import Store
from app.services.visit_service import _grant_points, _update_store_user_stats, REVIEW_POINTS
from app.schemas.review import ReviewCreateRequest, ReviewResponse, ReviewListResponse


async def create_review(
    db: AsyncSession,
    user_id: int,
    data: ReviewCreateRequest,
) -> ReviewResponse:
    """리뷰 작성 및 포인트 지급."""
    # Verify store exists
    result = await db.execute(select(Store).where(Store.id == data.store_id))
    store = result.scalar_one_or_none()
    if not store:
        raise ValueError("매장을 찾을 수 없습니다.")

    # Create review
    review = Review(
        user_id=user_id,
        store_id=data.store_id,
        visit_certification_id=data.visit_certification_id,
        rating=data.rating,
        content=data.content,
        earned_points=REVIEW_POINTS,
    )
    db.add(review)
    await db.flush()

    # Grant points
    await _grant_points(
        db, user_id, data.store_id, data.visit_certification_id, review.id,
        "review", REVIEW_POINTS, "리뷰 작성"
    )
    await _update_store_user_stats(db, user_id, data.store_id, REVIEW_POINTS, is_review=True)

    await db.refresh(review)

    # Get user info for response
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one()

    return ReviewResponse(
        id=review.id,
        user_id=review.user_id,
        store_id=review.store_id,
        visit_certification_id=review.visit_certification_id,
        rating=review.rating,
        content=review.content,
        earned_points=review.earned_points,
        created_at=review.created_at,
        updated_at=review.updated_at,
        user_nickname=user.nickname,
        user_profile_image_url=user.profile_image_url,
        store_name=store.name,
    )


async def get_store_reviews(
    db: AsyncSession,
    store_id: int,
    skip: int = 0,
    limit: int = 20,
) -> ReviewListResponse:
    """특정 매장의 리뷰 목록 조회."""
    # Total count
    count_result = await db.execute(
        select(func.count(Review.id)).where(Review.store_id == store_id)
    )
    total = count_result.scalar() or 0

    # Average rating
    avg_result = await db.execute(
        select(func.avg(Review.rating)).where(Review.store_id == store_id)
    )
    avg_rating = avg_result.scalar()

    # Reviews with user info
    result = await db.execute(
        select(Review, User.nickname, User.profile_image_url)
        .join(User, Review.user_id == User.id)
        .where(Review.store_id == store_id)
        .order_by(Review.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    rows = result.all()

    # Get store name
    store_result = await db.execute(select(Store.name).where(Store.id == store_id))
    store_name = store_result.scalar()

    reviews = [
        ReviewResponse(
            id=review.id,
            user_id=review.user_id,
            store_id=review.store_id,
            visit_certification_id=review.visit_certification_id,
            rating=review.rating,
            content=review.content,
            earned_points=review.earned_points,
            created_at=review.created_at,
            updated_at=review.updated_at,
            user_nickname=nickname,
            user_profile_image_url=profile_img,
            store_name=store_name,
        )
        for review, nickname, profile_img in rows
    ]

    return ReviewListResponse(
        reviews=reviews,
        total=total,
        average_rating=round(float(avg_rating), 1) if avg_rating else None,
    )


async def get_user_reviews(
    db: AsyncSession,
    user_id: int,
    skip: int = 0,
    limit: int = 20,
) -> ReviewListResponse:
    """특정 사용자의 리뷰 목록 조회."""
    count_result = await db.execute(
        select(func.count(Review.id)).where(Review.user_id == user_id)
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        select(Review, Store.name)
        .join(Store, Review.store_id == Store.id)
        .where(Review.user_id == user_id)
        .order_by(Review.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    rows = result.all()

    reviews = [
        ReviewResponse(
            id=review.id,
            user_id=review.user_id,
            store_id=review.store_id,
            visit_certification_id=review.visit_certification_id,
            rating=review.rating,
            content=review.content,
            earned_points=review.earned_points,
            created_at=review.created_at,
            updated_at=review.updated_at,
            store_name=store_name,
        )
        for review, store_name in rows
    ]

    return ReviewListResponse(reviews=reviews, total=total)
