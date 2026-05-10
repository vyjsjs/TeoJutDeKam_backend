from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class StoreResponse(BaseModel):
    id: int
    name: str
    category: Optional[str] = None
    address: str
    latitude: float
    longitude: float
    phone: Optional[str] = None
    image_url: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class StoreListResponse(BaseModel):
    stores: List[StoreResponse]
    total: int


class StoreDetailResponse(StoreResponse):
    """Store detail with 터줏대감 ranking and review summary."""
    total_visits: int = 0
    total_reviews: int = 0
    average_rating: Optional[float] = None


class StoreCreateRequest(BaseModel):
    name: str
    category: Optional[str] = None
    address: str
    latitude: float
    longitude: float
    phone: Optional[str] = None
    image_url: Optional[str] = None


class NearbyStoreRequest(BaseModel):
    latitude: float
    longitude: float
    radius_meters: int = 1000  # default 1km
