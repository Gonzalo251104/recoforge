"""Pydantic schemas for API request/response models."""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ============== Item Schemas ==============


class ItemResponse(BaseModel):
    """Response schema for a single item."""

    model_config = ConfigDict(populate_by_name=True)

    id: int
    title: str
    city: str
    priceMin: float = Field(alias="price_min")
    priceMax: float = Field(alias="price_max")
    tags: List[str]


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
    """Item in recommendation results."""

    id: int
    title: str
    city: str
    priceMin: float
    priceMax: float
    tags: List[str]


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
