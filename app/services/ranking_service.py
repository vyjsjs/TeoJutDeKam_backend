from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.models.store_user_stats import StoreUserStats
from app.models.user import User
from app.models.store import Store
from app.models.point_history import PointHistory
from app.schemas.ranking import (
    StoreUserStatsResponse,
    RankingResponse,
    GlobalRankingEntry,
    GlobalRankingResponse,
    PointHistoryResponse,
    PointHistoryListResponse,
)


async def get_store_ranking(
    db: AsyncSession,
    store_id: int,
    limit: int = 10,
) -> RankingResponse:
    """특정 매장의 터줏대감 순위 조회."""
    # Get store name
    store_result = await db.execute(select(Store).where(Store.id == store_id))
    store = store_result.scalar_one_or_none()
    if not store:
        raise ValueError("매장을 찾을 수 없습니다.")

    # Get rankings ordered by total_points desc
    result = await db.execute(
        select(StoreUserStats, User.nickname, User.profile_image_url)
        .join(User, StoreUserStats.user_id == User.id)
        .where(StoreUserStats.store_id == store_id)
        .order_by(desc(StoreUserStats.total_points))
        .limit(limit)
    )
    rows = result.all()

    rankings = [
        StoreUserStatsResponse(
            id=stats.id,
            user_id=stats.user_id,
            store_id=stats.store_id,
            total_points=stats.total_points,
            visit_count=stats.visit_count,
            review_count=stats.review_count,
            last_visited_at=stats.last_visited_at,
            user_nickname=nickname,
            user_profile_image_url=profile_img,
            store_name=store.name,
        )
        for stats, nickname, profile_img in rows
    ]

    return RankingResponse(
        store_id=store_id,
        store_name=store.name,
        rankings=rankings,
    )


async def get_global_ranking(
    db: AsyncSession,
    current_user_id: Optional[int] = None,
    limit: int = 50,
) -> GlobalRankingResponse:
    """전체 유저 포인트 순위 조회."""
    result = await db.execute(
        select(User.id, User.nickname, User.profile_image_url, User.total_points)
        .order_by(desc(User.total_points))
        .limit(limit)
    )
    rows = result.all()

    rankings = [
        GlobalRankingEntry(
            user_id=uid,
            nickname=nickname,
            profile_image_url=profile_img,
            total_points=total_points or 0,
            rank=idx + 1,
        )
        for idx, (uid, nickname, profile_img, total_points) in enumerate(rows)
    ]

    total_result = await db.execute(select(func.count(User.id)))
    total = total_result.scalar() or 0

    # Find current user's rank
    my_rank = None
    if current_user_id:
        for r in rankings:
            if r.user_id == current_user_id:
                my_rank = r.rank
                break
        if my_rank is None:
            # User is not in top N, calculate actual rank
            rank_result = await db.execute(
                select(func.count(User.id)).where(
                    User.total_points > (
                        select(User.total_points).where(User.id == current_user_id).scalar_subquery()
                    )
                )
            )
            my_rank = (rank_result.scalar() or 0) + 1

    return GlobalRankingResponse(
        rankings=rankings,
        total=total,
        my_rank=my_rank,
    )


async def get_user_store_stats(
    db: AsyncSession,
    user_id: int,
) -> list[StoreUserStatsResponse]:
    """유저의 매장별 활동 통계 (마이페이지용)."""
    result = await db.execute(
        select(StoreUserStats, Store.name)
        .join(Store, StoreUserStats.store_id == Store.id)
        .where(StoreUserStats.user_id == user_id)
        .order_by(desc(StoreUserStats.total_points))
    )
    rows = result.all()

    return [
        StoreUserStatsResponse(
            id=stats.id,
            user_id=stats.user_id,
            store_id=stats.store_id,
            total_points=stats.total_points,
            visit_count=stats.visit_count,
            review_count=stats.review_count,
            last_visited_at=stats.last_visited_at,
            store_name=store_name,
        )
        for stats, store_name in rows
    ]


async def get_user_point_history(
    db: AsyncSession,
    user_id: int,
    skip: int = 0,
    limit: int = 50,
) -> PointHistoryListResponse:
    """유저의 포인트 히스토리 조회."""
    count_result = await db.execute(
        select(func.count(PointHistory.id)).where(PointHistory.user_id == user_id)
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        select(PointHistory, Store.name)
        .outerjoin(Store, PointHistory.store_id == Store.id)
        .where(PointHistory.user_id == user_id)
        .order_by(desc(PointHistory.created_at))
        .offset(skip)
        .limit(limit)
    )
    rows = result.all()

    # Get total points
    user_result = await db.execute(
        select(func.sum(PointHistory.point_amount)).where(PointHistory.user_id == user_id)
    )
    total_points = user_result.scalar() or 0

    histories = [
        PointHistoryResponse(
            id=ph.id,
            user_id=ph.user_id,
            store_id=ph.store_id,
            point_type=ph.point_type,
            point_amount=ph.point_amount,
            description=ph.description,
            created_at=ph.created_at,
            store_name=store_name,
        )
        for ph, store_name in rows
    ]

    return PointHistoryListResponse(
        histories=histories,
        total=total,
        total_points=total_points,
    )
