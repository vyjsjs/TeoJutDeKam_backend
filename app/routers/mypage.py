from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdateRequest
from app.schemas.ranking import MyStoreStatsResponse, PointHistoryListResponse
from app.services.ranking_service import get_user_store_stats, get_user_point_history

router = APIRouter(prefix="/api/mypage", tags=["마이페이지"])


@router.get("/profile", response_model=UserResponse)
async def my_profile(current_user: User = Depends(get_current_user)):
    """내 프로필 조회"""
    return current_user


@router.put("/profile", response_model=UserResponse)
async def update_profile(
    data: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """내 프로필 수정"""
    if data.nickname is not None:
        current_user.nickname = data.nickname
    if data.profile_image_url is not None:
        current_user.profile_image_url = data.profile_image_url

    await db.flush()
    await db.refresh(current_user)
    return current_user


@router.get("/summary")
async def my_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """마이페이지 요약 정보"""
    from sqlalchemy import func
    from app.models.visit_certification import VisitCertification
    from app.models.review import Review
    from app.models.store_user_stats import StoreUserStats

    # 총 방문 인증 수
    visit_result = await db.execute(
        select(func.count(VisitCertification.id)).where(
            VisitCertification.user_id == current_user.id,
            VisitCertification.status == "approved",
        )
    )
    total_visits = visit_result.scalar() or 0

    # 총 리뷰 수
    review_result = await db.execute(
        select(func.count(Review.id)).where(Review.user_id == current_user.id)
    )
    total_reviews = review_result.scalar() or 0

    # 터줏대감인 매장 수 (해당 매장에서 1등인 경우)
    # Subquery: 각 매장에서 가장 높은 포인트를 가진 사용자
    from sqlalchemy import and_
    stats_result = await db.execute(
        select(StoreUserStats).where(StoreUserStats.user_id == current_user.id)
    )
    my_stats = stats_result.scalars().all()

    teojutdekam_count = 0
    for stat in my_stats:
        # Check if user is #1 at this store
        top_result = await db.execute(
            select(StoreUserStats.user_id)
            .where(StoreUserStats.store_id == stat.store_id)
            .order_by(StoreUserStats.total_points.desc())
            .limit(1)
        )
        top_user_id = top_result.scalar()
        if top_user_id == current_user.id:
            teojutdekam_count += 1

    return {
        "user": UserResponse.model_validate(current_user),
        "total_points": current_user.total_points or 0,
        "total_visits": total_visits,
        "total_reviews": total_reviews,
        "teojutdekam_stores": teojutdekam_count,
        "visited_stores_count": len(my_stats),
    }
