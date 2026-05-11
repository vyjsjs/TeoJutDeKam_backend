from fastapi import APIRouter, Depends

from app.core.database import supabase
from app.core.security import get_current_user
from app.schemas.user import UserResponse, UserUpdateRequest
from app.schemas.ranking import MyStoreStatsResponse, PointHistoryListResponse
from app.services.ranking_service import get_user_store_stats, get_user_point_history

router = APIRouter(prefix="/api/mypage", tags=["마이페이지"])


@router.get("/profile", response_model=UserResponse)
def my_profile(current_user: dict = Depends(get_current_user)):
    """내 프로필 조회"""
    return current_user


@router.put("/profile", response_model=UserResponse)
def update_profile(
    data: UserUpdateRequest,
    current_user: dict = Depends(get_current_user),
):
    """내 프로필 수정"""
    update_data = {}
    if data.nickname is not None:
        update_data["nickname"] = data.nickname
    if data.profile_image_url is not None:
        update_data["profile_image_url"] = data.profile_image_url

    if update_data:
        result = supabase.table("users").update(update_data).eq("id", current_user["id"]).execute()
        return result.data[0]
    return current_user


@router.get("/summary")
def my_summary(current_user: dict = Depends(get_current_user)):
    """마이페이지 요약 정보"""
    user_id = current_user["id"]

    # 총 방문 인증 수
    visit_result = supabase.table("visit_certifications") \
        .select("id", count="exact") \
        .eq("user_id", user_id) \
        .eq("status", "approved") \
        .execute()
    total_visits = visit_result.count or 0

    # 총 리뷰 수
    review_result = supabase.table("reviews") \
        .select("id", count="exact") \
        .eq("user_id", user_id) \
        .execute()
    total_reviews = review_result.count or 0

    # 터줏대감인 매장 수 (해당 매장에서 1등인 경우)
    stats_result = supabase.table("store_user_stats") \
        .select("store_id, total_points") \
        .eq("user_id", user_id) \
        .execute()
    my_stats = stats_result.data

    teojutdekam_count = 0
    for stat in my_stats:
        # Check if user is #1 at this store
        top_result = supabase.table("store_user_stats") \
            .select("user_id") \
            .eq("store_id", stat["store_id"]) \
            .order("total_points", desc=True) \
            .limit(1) \
            .execute()
        if top_result.data and top_result.data[0]["user_id"] == user_id:
            teojutdekam_count += 1

    return {
        "user": UserResponse(**current_user),
        "total_points": current_user.get("total_points", 0),
        "total_visits": total_visits,
        "total_reviews": total_reviews,
        "teojutdekam_stores": teojutdekam_count,
        "visited_stores_count": len(my_stats),
    }
