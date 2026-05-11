from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class VisitCertificationRequest(BaseModel):
    store_id: int
    user_latitude: float
    user_longitude: float
    certification_type: str = "gps"  # gps or receipt


class ReceiptCertificationRequest(BaseModel):
    store_id: int
    user_latitude: float
    user_longitude: float
    receipt_image_url: Optional[str] = None  # 하는 척만


class VisitCertificationResponse(BaseModel):
    id: int
    user_id: int
    store_id: int
    user_latitude: float
    user_longitude: float
    distance_meters: Optional[int] = None
    certification_type: str
    status: str
    earned_points: int
    certified_at: Optional[datetime] = None
    created_at: datetime
    store_name: Optional[str] = None

    model_config = {"from_attributes": True}
