from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.database import supabase
from app.core.security import get_current_user
from app.schemas.visit import (
    VisitCertificationRequest,
    ReceiptCertificationRequest,
    VisitCertificationResponse,
)
from app.services.visit_service import certify_visit_gps, certify_visit_receipt

router = APIRouter(prefix="/api/visits", tags=["방문 인증"])


@router.post("/gps", response_model=VisitCertificationResponse, status_code=status.HTTP_201_CREATED)
def certify_gps(
    data: VisitCertificationRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    GPS 기반 방문 인증.
    매장으로부터 50m 이내일 경우 자동 승인 및 포인트 지급.
    """
    try:
        cert = certify_visit_gps(
            current_user["id"], data.store_id, data.user_latitude, data.user_longitude
        )
        return VisitCertificationResponse(**cert)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/receipt", response_model=VisitCertificationResponse, status_code=status.HTTP_201_CREATED)
def certify_receipt(
    data: ReceiptCertificationRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    영수증 기반 방문 인증 (하는 척만).
    항상 승인 처리.
    """
    try:
        cert = certify_visit_receipt(
            current_user["id"], data.store_id,
            data.user_latitude, data.user_longitude,
            data.receipt_image_url,
        )
        return VisitCertificationResponse(**cert)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/my", response_model=list[VisitCertificationResponse])
def my_visit_certifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    """내 방문 인증 내역 조회"""
    result = supabase.table("visit_certifications") \
        .select("*, stores(name)") \
        .eq("user_id", current_user["id"]) \
        .order("created_at", desc=True) \
        .range(skip, skip + limit - 1) \
        .execute()

    certs = []
    for row in result.data:
        store_data = row.get("stores", {}) or {}
        cert = VisitCertificationResponse(
            id=row["id"],
            user_id=row["user_id"],
            store_id=row["store_id"],
            user_latitude=float(row["user_latitude"]),
            user_longitude=float(row["user_longitude"]),
            distance_meters=row.get("distance_meters"),
            certification_type=row["certification_type"],
            status=row["status"],
            earned_points=row["earned_points"],
            certified_at=row.get("certified_at"),
            created_at=row["created_at"],
            store_name=store_data.get("name"),
        )
        certs.append(cert)
    return certs
