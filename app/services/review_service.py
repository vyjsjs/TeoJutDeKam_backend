from app.core.database import supabase
from app.services.visit_service import _grant_points, _update_store_user_stats, REVIEW_POINTS
from app.schemas.review import ReviewCreateRequest, ReviewResponse, ReviewListResponse


def create_review(user_id: int, data: ReviewCreateRequest) -> ReviewResponse:
    """승인된 본인 방문 인증당 리뷰 1건 (ERD 1:1)."""
    store_result = supabase.table("stores").select("name").eq("id", data.store_id).execute()
    if not store_result.data:
        raise ValueError("매장을 찾을 수 없습니다.")
    store_name = store_result.data[0]["name"]

    cert_result = (
        supabase.table("visit_certifications")
        .select("*")
        .eq("id", data.visit_certification_id)
        .execute()
    )
    if not cert_result.data:
        raise ValueError("방문 인증을 찾을 수 없습니다.")
    cert = cert_result.data[0]

    if cert["user_id"] != user_id:
        raise ValueError("본인의 방문 인증만 리뷰에 연결할 수 있습니다.")
    if cert["store_id"] != data.store_id:
        raise ValueError("매장과 방문 인증이 일치하지 않습니다.")
    if cert["status"] != "approved":
        raise ValueError("승인된 방문만 리뷰를 작성할 수 있습니다.")

    dup = (
        supabase.table("reviews")
        .select("id")
        .eq("visit_certification_id", data.visit_certification_id)
        .execute()
    )
    if dup.data:
        raise ValueError("이 방문에 대한 리뷰가 이미 있습니다.")

    review_data = {
        "user_id": user_id,
        "store_id": data.store_id,
        "visit_certification_id": data.visit_certification_id,
        "rating": data.rating,
        "content": data.content,
        "earned_points": REVIEW_POINTS,
    }
    result = supabase.table("reviews").insert(review_data).execute()
    review = result.data[0]

    _grant_points(
        user_id,
        data.store_id,
        data.visit_certification_id,
        review["id"],
        "review",
        REVIEW_POINTS,
        "리뷰 작성",
    )
    _update_store_user_stats(user_id, data.store_id, REVIEW_POINTS, is_review=True)

    user_result = (
        supabase.table("users")
        .select("nickname, profile_image_url")
        .eq("id", user_id)
        .execute()
    )
    user = user_result.data[0]

    return ReviewResponse(
        id=review["id"],
        user_id=review["user_id"],
        store_id=review["store_id"],
        visit_certification_id=review["visit_certification_id"],
        rating=review["rating"],
        content=review.get("content"),
        earned_points=review["earned_points"],
        created_at=review["created_at"],
        updated_at=review["updated_at"],
        user_nickname=user["nickname"],
        user_profile_image_url=user.get("profile_image_url"),
        store_name=store_name,
    )


def get_store_reviews(store_id: int, skip: int = 0, limit: int = 20) -> ReviewListResponse:
    result = (
        supabase.table("reviews")
        .select("*, users(nickname, profile_image_url)")
        .eq("store_id", store_id)
        .order("created_at", desc=True)
        .range(skip, skip + limit - 1)
        .execute()
    )

    count_result = supabase.table("reviews").select("id", count="exact").eq("store_id", store_id).execute()
    total = count_result.count or 0

    all_ratings = supabase.table("reviews").select("rating").eq("store_id", store_id).execute()
    avg_rating = None
    if all_ratings.data:
        ratings = [r["rating"] for r in all_ratings.data]
        avg_rating = round(sum(ratings) / len(ratings), 1)

    store_result = supabase.table("stores").select("name").eq("id", store_id).execute()
    store_name = store_result.data[0]["name"] if store_result.data else None

    reviews = []
    for row in result.data:
        user_data = row.get("users", {}) or {}
        reviews.append(
            ReviewResponse(
                id=row["id"],
                user_id=row["user_id"],
                store_id=row["store_id"],
                visit_certification_id=row["visit_certification_id"],
                rating=row["rating"],
                content=row.get("content"),
                earned_points=row["earned_points"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                user_nickname=user_data.get("nickname"),
                user_profile_image_url=user_data.get("profile_image_url"),
                store_name=store_name,
            )
        )

    return ReviewListResponse(reviews=reviews, total=total, average_rating=avg_rating)


def get_user_reviews(user_id: int, skip: int = 0, limit: int = 20) -> ReviewListResponse:
    result = (
        supabase.table("reviews")
        .select("*, stores(name)")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .range(skip, skip + limit - 1)
        .execute()
    )

    count_result = supabase.table("reviews").select("id", count="exact").eq("user_id", user_id).execute()
    total = count_result.count or 0

    reviews = []
    for row in result.data:
        store_data = row.get("stores", {}) or {}
        reviews.append(
            ReviewResponse(
                id=row["id"],
                user_id=row["user_id"],
                store_id=row["store_id"],
                visit_certification_id=row["visit_certification_id"],
                rating=row["rating"],
                content=row.get("content"),
                earned_points=row["earned_points"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                store_name=store_data.get("name"),
            )
        )

    return ReviewListResponse(reviews=reviews, total=total)
