"""Pydantic schemas for API request/response models."""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ============== Item Schemas ==============


class ItemResponse(BaseModel):
    """Response schema for a single item."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    title: str
    description: str = ""
    city: str
    priceMin: float = Field(..., ge=0.0)
    priceMax: float = Field(..., ge=0.0)
    tags: List[str]


class CreateItemRequest(BaseModel):
    """Request schema for creating an item/activity."""
    model_config = ConfigDict(populate_by_name=True)

    title: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="")
    city: str = Field(..., min_length=1, max_length=50)
    priceMin: float = Field(..., ge=0.0)
    priceMax: float = Field(..., ge=0.0)
    tags: List[str] = Field(default_factory=list)


class UpdateItemRequest(BaseModel):
    """Request schema for updating an item/activity."""
    model_config = ConfigDict(populate_by_name=True)

    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None)
    city: Optional[str] = Field(None, min_length=1, max_length=50)
    priceMin: Optional[float] = Field(None, ge=0.0)
    priceMax: Optional[float] = Field(None, ge=0.0)
    tags: Optional[List[str]] = Field(None)



class ItemListResponse(BaseModel):
    """Paginated list of items."""

    page: int
    pageSize: int
    total: int
    results: List[ItemResponse]


# ============== Event Schemas ==============


class CreateEventRequest(BaseModel):
    """Request schema for creating an event/interaction."""

    userId: int = Field(..., ge=1)
    itemId: int = Field(..., ge=1)
    eventType: str = Field(..., pattern="^(view|click|save)$")


class EventResponse(BaseModel):
    """Response schema for a created event."""

    id: int
    userId: int
    itemId: int
    eventType: str
    ts: str


# ============== User History Schemas ==============


class HistoryItemResponse(BaseModel):
    """Item details within history."""

    id: int
    title: str
    description: str = ""
    city: str
    priceMin: float
    priceMax: float
    tags: List[str]


class HistoryEntryResponse(BaseModel):
    """Single history entry with event and item."""

    eventId: int
    eventType: str
    ts: Optional[str]
    item: HistoryItemResponse


class UserHistoryResponse(BaseModel):
    """User history response."""

    userId: int
    limit: int
    results: List[HistoryEntryResponse]


# ============== Recommendation Schemas ==============


class RecommendedItemResponse(BaseModel):
    """Item in recommendation results with match score and explainability description."""

    id: int
    title: str
    description: str = ""
    city: str
    priceMin: float
    priceMax: float
    tags: List[str]
    score: float
    explanation: str


class RecommendationsResponse(BaseModel):
    """Recommendations response."""

    userId: int
    strategy: str
    k: int
    results: List[RecommendedItemResponse]


# ============== Metrics Schemas ==============


class MetricsScores(BaseModel):
    """Metrics scores."""

    model_config = ConfigDict(populate_by_name=True)

    precision_at_k: float = Field(alias="precision@k")
    recall_at_k: float = Field(alias="recall@k")


class OfflineMetricsResponse(BaseModel):
    """Offline evaluation metrics response."""

    strategy: str
    k: int
    usersEvaluated: int
    metrics: MetricsScores


# ============== Health Schemas ==============


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    app: str
    env: str


# ============== User Schemas ==============


class UserResponse(BaseModel):
    """Response schema for a single user."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    username: str
    createdAt: str = Field(alias="created_at")


class UserStats(BaseModel):
    """Calculated statistics for user interactions."""

    totalViews: int
    totalClicks: int
    totalSaves: int
    favoriteTags: List[str]


class UserProfileResponse(BaseModel):
    """Detailed user profile response with statistics."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    username: str
    createdAt: str = Field(alias="created_at")
    stats: UserStats


class UserListResponse(BaseModel):
    """Paginated list of users."""

    page: int
    pageSize: int
    total: int
    results: List[UserResponse]


class CreateUserRequest(BaseModel):
    """Request schema for creating a user."""

    username: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_-]+$")


# ============== Event List Schemas ==============


class EventListEntry(BaseModel):
    """Single event entry in list."""

    id: int
    userId: int
    itemId: int
    eventType: str
    ts: str
    itemTitle: str
    itemCity: str


class EventListResponse(BaseModel):
    """Paginated list of interaction events."""

    page: int
    pageSize: int
    total: int
    results: List[EventListEntry]
