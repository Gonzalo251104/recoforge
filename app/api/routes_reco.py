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
from app.reco.popular import recommend_popular
from app.reco.explainability import generate_explanation

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

SUPPORTED_STRATEGIES = {"content", "user", "hybrid", "popular"}


@router.get("/{user_id}", response_model=RecommendationsResponse)
def get_recommendations(
    user_id: int,
    strategy: str = Query("content", description="Recommendation strategy: content, user, hybrid, popular"),
    k: int = Query(10, ge=1, le=100, description="Number of recommendations"),
    content_weight: float = Query(0.5, ge=0.0, le=1.0, description="Weight for content-based in hybrid"),
    user_weight: float = Query(0.5, ge=0.0, le=1.0, description="Weight for user-based in hybrid"),
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

    strategy_used = strategy
    items_with_scores = []

    if strategy == "content":
        items_with_scores = recommend_content_based(session=session, user_id=user_id, k=k)
        if not items_with_scores:
            items_with_scores = recommend_popular(session=session, user_id=user_id, k=k)
            strategy_used = "popular"
    elif strategy == "user":
        items_with_scores = recommend_user_based(session=session, user_id=user_id, k=k)
        if not items_with_scores:
            items_with_scores = recommend_popular(session=session, user_id=user_id, k=k)
            strategy_used = "popular"
    elif strategy == "hybrid":
        items_with_scores = recommend_hybrid(
            session=session,
            user_id=user_id,
            k=k,
            content_weight=content_weight,
            user_weight=user_weight
        )
        if not items_with_scores:
            items_with_scores = recommend_popular(session=session, user_id=user_id, k=k)
            strategy_used = "popular"
    elif strategy == "popular":
        items_with_scores = recommend_popular(session=session, user_id=user_id, k=k)

    results = []
    for it, raw_score in items_with_scores:
        if it.id is None:
            continue
        
        # Format scores to standard range/decimals
        score = round(float(raw_score), 4)
        explanation = generate_explanation(session, user_id, it.id, strategy_used, score)
        
        results.append(
            RecommendedItemResponse(
                id=it.id,
                title=it.title,
                city=it.city,
                priceMin=it.price_min,
                priceMax=it.price_max,
                tags=parse_tags(it.tags_json),
                score=score,
                explanation=explanation,
            )
        )

    return RecommendationsResponse(
        userId=user_id,
        strategy=strategy_used,
        k=k,
        results=results,
    )
