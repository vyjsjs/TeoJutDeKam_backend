import math
from datetime import datetime, timezone
from typing import Optional

from app.core.database import supabase


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points
    on Earth using the Haversine formula. Returns distance in meters.
    """
    R = 6371000  # Earth's radius in meters

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


VISIT_POINTS = 10
REVIEW_POINTS = 5
MAX_VISIT_DISTANCE_METERS = 50


def certify_visit_gps(
    user_id: int,
    store_id: int,
    user_lat: float,
    user_lng: float,
) -> dict:
    """
    GPS 기반 방문 인증.
    매장으로부터 50m 이내일 경우 자동 승인 및 포인트 지급.
    """
    # Get store
    result = supabase.table("stores").select("*").eq("id", store_id).execute()
    if not result.data:
        raise ValueError("매장을 찾을 수 없습니다.")
    store = result.data[0]

    # Calculate distance
    distance = haversine_distance(
        user_lat, user_lng,
        float(store["latitude"]), float(store["longitude"])
    )
    distance_int = int(distance)

    # Determine status
    now_str = datetime.now(timezone.utc).isoformat()
    if distance_int <= MAX_VISIT_DISTANCE_METERS:
        status = "approved"
        earned_points = VISIT_POINTS
        certified_at = now_str
    else:
        status = "rejected"
        earned_points = 0
        certified_at = None

    # Create certification
    cert_data = {
        "user_id": user_id,
        "store_id": store_id,
        "user_latitude": user_lat,
        "user_longitude": user_lng,
        "distance_meters": distance_int,
        "certification_type": "gps",
        "status": status,
        "earned_points": earned_points,
        "certified_at": certified_at,
    }
    cert_result = supabase.table("visit_certifications").insert(cert_data).execute()
    cert = cert_result.data[0]

    # If approved, update points and stats
    if status == "approved":
        _grant_points(user_id, store_id, cert["id"], None, "visit", earned_points, "GPS 방문 인증")
        _update_store_user_stats(user_id, store_id, earned_points, is_visit=True)

    return cert


def certify_visit_receipt(
    user_id: int,
    store_id: int,
    user_lat: float,
    user_lng: float,
    receipt_image_url: Optional[str] = None,
) -> dict:
    """
    영수증 방문 인증 (하는 척만).
    항상 승인 처리하여 포인트 지급.
    """
    result = supabase.table("stores").select("*").eq("id", store_id).execute()
    if not result.data:
        raise ValueError("매장을 찾을 수 없습니다.")
    store = result.data[0]

    distance = haversine_distance(
        user_lat, user_lng,
        float(store["latitude"]), float(store["longitude"])
    )
    distance_int = int(distance)

    now_str = datetime.now(timezone.utc).isoformat()
    earned_points = VISIT_POINTS
    cert_data = {
        "user_id": user_id,
        "store_id": store_id,
        "user_latitude": user_lat,
        "user_longitude": user_lng,
        "distance_meters": distance_int,
        "certification_type": "receipt",
        "status": "approved",
        "earned_points": earned_points,
        "certified_at": now_str,
    }
    cert_result = supabase.table("visit_certifications").insert(cert_data).execute()
    cert = cert_result.data[0]

    _grant_points(user_id, store_id, cert["id"], None, "visit", earned_points, "영수증 방문 인증")
    _update_store_user_stats(user_id, store_id, earned_points, is_visit=True)

    return cert


def _grant_points(
    user_id: int,
    store_id: int,
    visit_cert_id: Optional[int],
    review_id: Optional[int],
    point_type: str,
    amount: int,
    description: str,
):
    """포인트 지급 및 히스토리 기록."""
    history_data = {
        "user_id": user_id,
        "store_id": store_id,
        "visit_certification_id": visit_cert_id,
        "review_id": review_id,
        "point_type": point_type,
        "point_amount": amount,
        "description": description,
    }
    supabase.table("point_histories").insert(history_data).execute()

    # Update user total points
    user_result = supabase.table("users").select("total_points").eq("id", user_id).execute()
    current_points = user_result.data[0]["total_points"] or 0
    supabase.table("users").update({"total_points": current_points + amount}).eq("id", user_id).execute()


def _update_store_user_stats(
    user_id: int,
    store_id: int,
    points: int,
    is_visit: bool = False,
    is_review: bool = False,
):
    """매장별 유저 통계 업데이트 (터줏대감 순위용)."""
    result = supabase.table("store_user_stats") \
        .select("*") \
        .eq("user_id", user_id) \
        .eq("store_id", store_id) \
        .execute()

    now_str = datetime.now(timezone.utc).isoformat()

    if not result.data:
        # Create new stats
        stats_data = {
            "user_id": user_id,
            "store_id": store_id,
            "total_points": points,
            "visit_count": 1 if is_visit else 0,
            "review_count": 1 if is_review else 0,
            "last_visited_at": now_str if is_visit else None,
        }
        supabase.table("store_user_stats").insert(stats_data).execute()
    else:
        stats = result.data[0]
        update_data = {
            "total_points": (stats["total_points"] or 0) + points,
        }
        if is_visit:
            update_data["visit_count"] = (stats["visit_count"] or 0) + 1
            update_data["last_visited_at"] = now_str
        if is_review:
            update_data["review_count"] = (stats["review_count"] or 0) + 1

        supabase.table("store_user_stats").update(update_data).eq("id", stats["id"]).execute()
