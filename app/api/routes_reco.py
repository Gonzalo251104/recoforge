from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.api.schemas import RecommendationsResponse, RecommendedItemResponse
from app.core.utils import parse_tags
from app.db.models import Item, User
from app.db.session import get_session
from app.reco.content_based import recommend_content_based
from app.reco.user_based import recommend_user_based
from app.reco.hybrid import recommend_hybrid

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

SUPPORTED_STRATEGIES = {"content", "user", "hybrid"}


def _items_to_response(items: List[Item]) -> List[RecommendedItemResponse]:
    return [
        RecommendedItemResponse(
            id=it.id,
            title=it.title,
            city=it.city,
            priceMin=it.price_min,
            priceMax=it.price_max,
            tags=parse_tags(it.tags_json),
        )
        for it in items
        if it.id is not None
    ]


@router.get("/{user_id}", response_model=RecommendationsResponse)
def get_recommendations(
    user_id: int,
    strategy: str = Query("content", description="Recommendation strategy: content, user, hybrid"),
    k: int = Query(10, ge=1, le=100, description="Number of recommendations"),
    session: Session = Depends(get_session),
):
    user = session.exec(select(User).where(User.id == user_id)).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if strategy not in SUPPORTED_STRATEGIES:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown strategy '{strategy}'. Supported: {', '.join(sorted(SUPPORTED_STRATEGIES))}",
        )

    if strategy == "content":
        items = recommend_content_based(session=session, user_id=user_id, k=k)
    elif strategy == "user":
        items = recommend_user_based(session=session, user_id=user_id, k=k)
    elif strategy == "hybrid":
        items = recommend_hybrid(session=session, user_id=user_id, k=k)

    return RecommendationsResponse(
        userId=user_id,
        strategy=strategy,
        k=k,
        results=_items_to_response(items),
    )
