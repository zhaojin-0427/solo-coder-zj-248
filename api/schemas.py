from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    role: str
    avatar: str = ""
    created_at: datetime

    class Config:
        from_attributes = True


class KitListingCreate(BaseModel):
    user_id: int
    title: str
    type: str
    scale: str
    manufacturer: str = ""
    condition: str = "sealed"
    missing_parts: str = ""
    subject: str
    price: float = 0.0
    description: str = ""
    images: List[str] = []


class KitListingOut(BaseModel):
    id: int
    user_id: int
    title: str
    type: str
    scale: str
    manufacturer: str
    condition: str
    missing_parts: str
    subject: str
    price: float
    description: str
    images: List
    status: str
    favorites: int
    created_at: datetime

    class Config:
        from_attributes = True


class KitMatchOut(BaseModel):
    id: int
    sell_listing_id: int
    buy_listing_id: int
    match_score: float
    created_at: datetime

    class Config:
        from_attributes = True


class ListingStatusUpdate(BaseModel):
    status: str


class TutorialStepOut(BaseModel):
    id: int
    tutorial_id: int
    order_num: int
    title: str
    description: str
    image: str
    technique: str

    class Config:
        from_attributes = True


class PaintRecordOut(BaseModel):
    id: int
    tutorial_id: int
    name: str
    brand: str
    color_code: str
    usage: str

    class Config:
        from_attributes = True


class WeatheringDetailOut(BaseModel):
    id: int
    tutorial_id: int
    type: str
    products: List
    technique: str
    description: str

    class Config:
        from_attributes = True


class TutorialStepCreate(BaseModel):
    order_num: int
    title: str
    description: str
    technique: str = ""
    image: str = ""


class PaintRecordCreate(BaseModel):
    name: str
    brand: str
    color_code: str = ""
    usage: str = ""


class WeatheringDetailCreate(BaseModel):
    type: str
    products: List[str] = []
    technique: str = ""
    description: str = ""


class TutorialCreate(BaseModel):
    user_id: int
    title: str
    subject: str
    difficulty: str = "beginner"
    cover_image: str = ""
    steps: List[TutorialStepCreate] = []
    paints: List[PaintRecordCreate] = []
    weathering_details: List[WeatheringDetailCreate] = []


class TutorialOut(BaseModel):
    id: int
    user_id: int
    title: str
    subject: str
    difficulty: str
    cover_image: str
    views: int
    completions: int
    favorites: int
    created_at: datetime
    steps: List[TutorialStepOut] = []
    paints: List[PaintRecordOut] = []
    weathering_details: List[WeatheringDetailOut] = []

    class Config:
        from_attributes = True


class TutorialSummaryOut(BaseModel):
    id: int
    user_id: int
    title: str
    subject: str
    difficulty: str
    cover_image: str
    views: int
    completions: int
    favorites: int
    created_at: datetime

    class Config:
        from_attributes = True


class ArtworkCreate(BaseModel):
    user_id: int
    title: str
    subject: str
    scale: str = ""
    kit_name: str = ""
    images: List[str] = []
    paints: List[str] = []
    techniques: List[str] = []
    weathering: List[str] = []


class ArtworkOut(BaseModel):
    id: int
    user_id: int
    title: str
    subject: str
    scale: str
    kit_name: str
    images: List
    paints: List
    techniques: List
    weathering: List
    likes: int
    favorites: int
    created_at: datetime

    class Config:
        from_attributes = True


class ToolOut(BaseModel):
    id: int
    name: str
    category: str
    brand: str
    rating: float
    review_count: int
    description: str
    image: str
    recommended_by: List

    class Config:
        from_attributes = True


class FavoriteCreate(BaseModel):
    user_id: int
    target_type: str
    target_id: int


class FavoriteOut(BaseModel):
    id: int
    user_id: int
    target_type: str
    target_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class PopularSubjectOut(BaseModel):
    scale: str
    subject: str
    count: int


class TurnoverSpeedOut(BaseModel):
    month: str
    avg_days: float


class TutorialCompletionOut(BaseModel):
    tutorial_id: int
    title: str
    views: int
    completions: int
    completion_rate: float


class TechniqueFavoriteOut(BaseModel):
    technique: str
    favorite_count: int
