from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ReviewCreateRequest(BaseModel):
    store_id: int
    visit_certification_id: Optional[int] = None
    rating: int  # 1-5
    content: Optional[str] = None


class ReviewResponse(BaseModel):
    id: int
    user_id: int
    store_id: int
    visit_certification_id: Optional[int] = None
    rating: int
    content: Optional[str] = None
    earned_points: int
    created_at: datetime
    updated_at: datetime
    # joined fields
    user_nickname: Optional[str] = None
    user_profile_image_url: Optional[str] = None
    store_name: Optional[str] = None

    model_config = {"from_attributes": True}


class ReviewListResponse(BaseModel):
    reviews: List[ReviewResponse]
    total: int
    average_rating: Optional[float] = None
