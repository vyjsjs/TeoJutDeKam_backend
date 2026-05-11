from typing import Optional

from app.core.database import supabase
from app.schemas.ranking import (
    StoreUserStatsResponse,
    RankingResponse,
    GlobalRankingEntry,
    GlobalRankingResponse,
    PointHistoryResponse,
    PointHistoryListResponse,
)


def get_store_ranking(store_id: int, limit: int = 10) -> RankingResponse:
    """특정 매장의 터줏대감 순위 조회."""
    # Get store name
    store_result = supabase.table("stores").select("name").eq("id", store_id).execute()
    if not store_result.data:
        raise ValueError("매장을 찾을 수 없습니다.")
    store_name = store_result.data[0]["name"]

    # Get rankings
    result = supabase.table("store_user_stats") \
        .select("*, users(nickname, profile_image_url)") \
        .eq("store_id", store_id) \
        .order("total_points", desc=True) \
        .limit(limit) \
        .execute()

    rankings = []
    for row in result.data:
        user_data = row.get("users", {}) or {}
        rankings.append(StoreUserStatsResponse(
            id=row["id"],
            user_id=row["user_id"],
            store_id=row["store_id"],
            total_points=row["total_points"],
            visit_count=row["visit_count"],
            review_count=row["review_count"],
            last_visited_at=row.get("last_visited_at"),
            user_nickname=user_data.get("nickname"),
            user_profile_image_url=user_data.get("profile_image_url"),
            store_name=store_name,
        ))

    return RankingResponse(store_id=store_id, store_name=store_name, rankings=rankings)


def get_global_ranking(
    current_user_id: Optional[int] = None,
    limit: int = 50,
) -> GlobalRankingResponse:
    """전체 유저 포인트 순위 조회."""
    result = supabase.table("users") \
        .select("id, nickname, profile_image_url, total_points") \
        .order("total_points", desc=True) \
        .limit(limit) \
        .execute()

    rankings = [
        GlobalRankingEntry(
            user_id=row["id"],
            nickname=row["nickname"],
            profile_image_url=row.get("profile_image_url"),
            total_points=row["total_points"] or 0,
            rank=idx + 1,
        )
        for idx, row in enumerate(result.data)
    ]

    # Total users
    count_result = supabase.table("users").select("id", count="exact").execute()
    total = count_result.count or 0

    # Find current user's rank
    my_rank = None
    if current_user_id:
        for r in rankings:
            if r.user_id == current_user_id:
                my_rank = r.rank
                break
        if my_rank is None:
            # User is not in top N — count users with more points
            user_result = supabase.table("users").select("total_points").eq("id", current_user_id).execute()
            if user_result.data:
                my_points = user_result.data[0]["total_points"] or 0
                higher = supabase.table("users") \
                    .select("id", count="exact") \
                    .gt("total_points", my_points) \
                    .execute()
                my_rank = (higher.count or 0) + 1

    return GlobalRankingResponse(rankings=rankings, total=total, my_rank=my_rank)


def get_user_store_stats(user_id: int) -> list[StoreUserStatsResponse]:
    """유저의 매장별 활동 통계 (마이페이지용)."""
    result = supabase.table("store_user_stats") \
        .select("*, stores(name)") \
        .eq("user_id", user_id) \
        .order("total_points", desc=True) \
        .execute()

    stats_list = []
    for row in result.data:
        store_data = row.get("stores", {}) or {}
        stats_list.append(StoreUserStatsResponse(
            id=row["id"],
            user_id=row["user_id"],
            store_id=row["store_id"],
            total_points=row["total_points"],
            visit_count=row["visit_count"],
            review_count=row["review_count"],
            last_visited_at=row.get("last_visited_at"),
            store_name=store_data.get("name"),
        ))
    return stats_list


def get_user_point_history(
    user_id: int,
    skip: int = 0,
    limit: int = 50,
) -> PointHistoryListResponse:
    """유저의 포인트 히스토리 조회."""
    # Count
    count_result = supabase.table("point_histories") \
        .select("id", count="exact") \
        .eq("user_id", user_id) \
        .execute()
    total = count_result.count or 0

    # Get histories with store name
    result = supabase.table("point_histories") \
        .select("*, stores(name)") \
        .eq("user_id", user_id) \
        .order("created_at", desc=True) \
        .range(skip, skip + limit - 1) \
        .execute()

    # Total points
    user_result = supabase.table("users").select("total_points").eq("id", user_id).execute()
    total_points = user_result.data[0]["total_points"] if user_result.data else 0

    histories = []
    for row in result.data:
        store_data = row.get("stores", {}) or {}
        histories.append(PointHistoryResponse(
            id=row["id"],
            user_id=row["user_id"],
            store_id=row.get("store_id"),
            point_type=row["point_type"],
            point_amount=row["point_amount"],
            description=row.get("description"),
            created_at=row["created_at"],
            store_name=store_data.get("name"),
        ))

    return PointHistoryListResponse(histories=histories, total=total, total_points=total_points)
