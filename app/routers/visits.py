from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.visit_certification import VisitCertification
from app.schemas.visit import (
    VisitCertificationRequest,
    ReceiptCertificationRequest,
    VisitCertificationResponse,
)
from app.services.visit_service import certify_visit_gps, certify_visit_receipt

router = APIRouter(prefix="/api/visits", tags=["방문 인증"])


@router.post("/gps", response_model=VisitCertificationResponse, status_code=status.HTTP_201_CREATED)
async def certify_gps(
    data: VisitCertificationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    GPS 기반 방문 인증.
    매장으로부터 50m 이내일 경우 자동 승인 및 포인트 지급.
    """
    try:
        cert = await certify_visit_gps(
            db, current_user.id, data.store_id, data.user_latitude, data.user_longitude
        )

        if cert.status == "rejected":
            return VisitCertificationResponse(
                id=cert.id,
                user_id=cert.user_id,
                store_id=cert.store_id,
                user_latitude=float(cert.user_latitude),
                user_longitude=float(cert.user_longitude),
                distance_meters=cert.distance_meters,
                certification_type=cert.certification_type,
                status=cert.status,
                earned_points=cert.earned_points,
                certified_at=cert.certified_at,
                created_at=cert.created_at,
            )

        return VisitCertificationResponse(
            id=cert.id,
            user_id=cert.user_id,
            store_id=cert.store_id,
            user_latitude=float(cert.user_latitude),
            user_longitude=float(cert.user_longitude),
            distance_meters=cert.distance_meters,
            certification_type=cert.certification_type,
            status=cert.status,
            earned_points=cert.earned_points,
            certified_at=cert.certified_at,
            created_at=cert.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/receipt", response_model=VisitCertificationResponse, status_code=status.HTTP_201_CREATED)
async def certify_receipt(
    data: ReceiptCertificationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    영수증 기반 방문 인증 (하는 척만).
    항상 승인 처리.
    """
    try:
        cert = await certify_visit_receipt(
            db, current_user.id, data.store_id,
            data.user_latitude, data.user_longitude,
            data.receipt_image_url,
        )
        return VisitCertificationResponse(
            id=cert.id,
            user_id=cert.user_id,
            store_id=cert.store_id,
            user_latitude=float(cert.user_latitude),
            user_longitude=float(cert.user_longitude),
            distance_meters=cert.distance_meters,
            certification_type=cert.certification_type,
            status=cert.status,
            earned_points=cert.earned_points,
            certified_at=cert.certified_at,
            created_at=cert.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/my", response_model=list[VisitCertificationResponse])
async def my_visit_certifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """내 방문 인증 내역 조회"""
    from app.models.store import Store

    result = await db.execute(
        select(VisitCertification, Store.name)
        .outerjoin(Store, VisitCertification.store_id == Store.id)
        .where(VisitCertification.user_id == current_user.id)
        .order_by(VisitCertification.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    rows = result.all()

    return [
        VisitCertificationResponse(
            id=cert.id,
            user_id=cert.user_id,
            store_id=cert.store_id,
            user_latitude=float(cert.user_latitude),
            user_longitude=float(cert.user_longitude),
            distance_meters=cert.distance_meters,
            certification_type=cert.certification_type,
            status=cert.status,
            earned_points=cert.earned_points,
            certified_at=cert.certified_at,
            created_at=cert.created_at,
            store_name=store_name,
        )
        for cert, store_name in rows
    ]
