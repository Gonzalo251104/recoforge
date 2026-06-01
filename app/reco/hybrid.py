"""Hybrid recommendation engine combining content-based and user-based approaches.

This module implements a weighted hybrid strategy that combines scores from
content-based and user-based collaborative filtering.
"""

from collections import defaultdict
from typing import Dict, List, Set

from sqlmodel import Session, col, select

from app.db.models import Interaction, Item
from app.reco.content_based import recommend_content_based
from app.reco.user_based import recommend_user_based


def recommend_hybrid(
    session: Session,
    user_id: int,
    k: int = 10,
    content_weight: float = 0.5,
    user_weight: float = 0.5,
    fetch_multiplier: int = 3,
) -> List[Item]:
    """
    Recommend items using a hybrid approach combining content-based and user-based filtering.

    Args:
        session: Database session.
        user_id: Target user ID.
        k: Number of recommendations to return.
        content_weight: Weight for content-based scores (0-1).
        user_weight: Weight for user-based scores (0-1).
        fetch_multiplier: Fetch k * multiplier from each strategy to ensure variety.

    Returns:
        List of recommended Item objects.
    """
    fetch_k = k * fetch_multiplier

    # Get recommendations from both strategies
    content_items = recommend_content_based(session=session, user_id=user_id, k=fetch_k)
    user_items = recommend_user_based(session=session, user_id=user_id, k=fetch_k)

    # Items the user has already seen
    seen_stmt = select(Interaction.item_id).where(Interaction.user_id == user_id)
    seen_ids: Set[int] = {row for row in session.exec(seen_stmt).all()}

    # Score aggregation: use rank-based scoring (higher rank = higher score)
    item_scores: Dict[int, float] = defaultdict(float)

    # Content-based scoring (rank-based: first item gets highest score)
    for rank, item in enumerate(content_items):
        if item.id is None or item.id in seen_ids:
            continue
        # Normalize rank to 0-1 range (higher is better)
        rank_score = 1.0 - (rank / max(len(content_items), 1))
        item_scores[item.id] += content_weight * rank_score

    # User-based scoring
    for rank, item in enumerate(user_items):
        if item.id is None or item.id in seen_ids:
            continue
        rank_score = 1.0 - (rank / max(len(user_items), 1))
        item_scores[item.id] += user_weight * rank_score

    if not item_scores:
        # Fallback: return content-based results if available
        return content_items[:k]

    # Sort by combined score
    sorted_item_ids = sorted(item_scores.items(), key=lambda x: x[1], reverse=True)
    top_item_ids = [item_id for item_id, _ in sorted_item_ids[:k]]

    if not top_item_ids:
        return []

    # Fetch Item objects
    stmt = select(Item).where(col(Item.id).in_(top_item_ids))
    items = session.exec(stmt).all()

    # Preserve score order
    item_map = {it.id: it for it in items}
    return [item_map[iid] for iid in top_item_ids if iid in item_map]
