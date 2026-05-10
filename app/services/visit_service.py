import math
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.store import Store
from app.models.visit_certification import VisitCertification
from app.models.review import Review
from app.models.store_user_stats import StoreUserStats
from app.models.point_history import PointHistory
from app.models.user import User


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


async def certify_visit_gps(
    db: AsyncSession,
    user_id: int,
    store_id: int,
    user_lat: float,
    user_lng: float,
) -> VisitCertification:
    """
    GPS 기반 방문 인증.
    매장으로부터 50m 이내일 경우 자동 승인 및 포인트 지급.
    """
    # Get store
    result = await db.execute(select(Store).where(Store.id == store_id))
    store = result.scalar_one_or_none()
    if not store:
        raise ValueError("매장을 찾을 수 없습니다.")

    # Calculate distance
    distance = haversine_distance(
        user_lat, user_lng,
        float(store.latitude), float(store.longitude)
    )
    distance_int = int(distance)

    # Determine status
    if distance_int <= MAX_VISIT_DISTANCE_METERS:
        status = "approved"
        earned_points = VISIT_POINTS
        certified_at = datetime.now(timezone.utc)
    else:
        status = "rejected"
        earned_points = 0
        certified_at = None

    # Create certification
    certification = VisitCertification(
        user_id=user_id,
        store_id=store_id,
        user_latitude=user_lat,
        user_longitude=user_lng,
        distance_meters=distance_int,
        certification_type="gps",
        status=status,
        earned_points=earned_points,
        certified_at=certified_at,
    )
    db.add(certification)
    await db.flush()

    # If approved, update points and stats
    if status == "approved":
        await _grant_points(db, user_id, store_id, certification.id, None, "visit", earned_points, "GPS 방문 인증")
        await _update_store_user_stats(db, user_id, store_id, earned_points, is_visit=True)

    await db.refresh(certification)
    return certification


async def certify_visit_receipt(
    db: AsyncSession,
    user_id: int,
    store_id: int,
    user_lat: float,
    user_lng: float,
    receipt_image_url: Optional[str] = None,
) -> VisitCertification:
    """
    영수증 방문 인증 (하는 척만).
    항상 승인 처리하여 포인트 지급.
    """
    result = await db.execute(select(Store).where(Store.id == store_id))
    store = result.scalar_one_or_none()
    if not store:
        raise ValueError("매장을 찾을 수 없습니다.")

    distance = haversine_distance(
        user_lat, user_lng,
        float(store.latitude), float(store.longitude)
    )
    distance_int = int(distance)

    # 영수증 인증은 항상 승인 (하는 척)
    earned_points = VISIT_POINTS
    certification = VisitCertification(
        user_id=user_id,
        store_id=store_id,
        user_latitude=user_lat,
        user_longitude=user_lng,
        distance_meters=distance_int,
        certification_type="receipt",
        status="approved",
        earned_points=earned_points,
        certified_at=datetime.now(timezone.utc),
    )
    db.add(certification)
    await db.flush()

    await _grant_points(db, user_id, store_id, certification.id, None, "visit", earned_points, "영수증 방문 인증")
    await _update_store_user_stats(db, user_id, store_id, earned_points, is_visit=True)

    await db.refresh(certification)
    return certification


async def _grant_points(
    db: AsyncSession,
    user_id: int,
    store_id: int,
    visit_cert_id: Optional[int],
    review_id: Optional[int],
    point_type: str,
    amount: int,
    description: str,
):
    """포인트 지급 및 히스토리 기록."""
    # Create point history
    history = PointHistory(
        user_id=user_id,
        store_id=store_id,
        visit_certification_id=visit_cert_id,
        review_id=review_id,
        point_type=point_type,
        point_amount=amount,
        description=description,
    )
    db.add(history)

    # Update user total points
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one()
    user.total_points = (user.total_points or 0) + amount
    await db.flush()


async def _update_store_user_stats(
    db: AsyncSession,
    user_id: int,
    store_id: int,
    points: int,
    is_visit: bool = False,
    is_review: bool = False,
):
    """매장별 유저 통계 업데이트 (터줏대감 순위용)."""
    result = await db.execute(
        select(StoreUserStats).where(
            StoreUserStats.user_id == user_id,
            StoreUserStats.store_id == store_id,
        )
    )
    stats = result.scalar_one_or_none()

    if not stats:
        stats = StoreUserStats(
            user_id=user_id,
            store_id=store_id,
            total_points=0,
            visit_count=0,
            review_count=0,
        )
        db.add(stats)

    stats.total_points = (stats.total_points or 0) + points
    if is_visit:
        stats.visit_count = (stats.visit_count or 0) + 1
        stats.last_visited_at = datetime.now(timezone.utc)
    if is_review:
        stats.review_count = (stats.review_count or 0) + 1

    await db.flush()
