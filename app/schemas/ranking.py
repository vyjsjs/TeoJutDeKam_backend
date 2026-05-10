from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class PointHistoryResponse(BaseModel):
    id: int
    user_id: int
    store_id: Optional[int] = None
    point_type: str
    point_amount: int
    description: Optional[str] = None
    created_at: datetime
    store_name: Optional[str] = None

    model_config = {"from_attributes": True}


class PointHistoryListResponse(BaseModel):
    histories: List[PointHistoryResponse]
    total: int
    total_points: int


# ─── Ranking / 터줏대감 ─────────────────────────────────
class StoreUserStatsResponse(BaseModel):
    id: int
    user_id: int
    store_id: int
    total_points: int
    visit_count: int
    review_count: int
    last_visited_at: Optional[datetime] = None
    # joined
    user_nickname: Optional[str] = None
    user_profile_image_url: Optional[str] = None
    store_name: Optional[str] = None

    model_config = {"from_attributes": True}


class RankingResponse(BaseModel):
    """특정 매장의 터줏대감 순위"""
    store_id: int
    store_name: str
    rankings: List[StoreUserStatsResponse]


class MyStoreStatsResponse(BaseModel):
    """내가 터줏대감인 매장 목록"""
    stores: List[StoreUserStatsResponse]
    total: int


class GlobalRankingEntry(BaseModel):
    user_id: int
    nickname: str
    profile_image_url: Optional[str] = None
    total_points: int
    rank: int


class GlobalRankingResponse(BaseModel):
    rankings: List[GlobalRankingEntry]
    total: int
    my_rank: Optional[int] = None
