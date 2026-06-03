from collections import defaultdict
from typing import Dict, List, Set, Tuple

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
) -> List[Tuple[Item, float]]:
    """
    Recommend items using a hybrid approach combining content-based and user-based filtering.
    Returns recommended items with aggregated scores.
    """
    fetch_k = k * fetch_multiplier

    # Get recommendations with scores from both strategies
    content_items = recommend_content_based(session=session, user_id=user_id, k=fetch_k)
    user_items = recommend_user_based(session=session, user_id=user_id, k=fetch_k)

    # Items the user has already seen
    seen_stmt = select(Interaction.item_id).where(Interaction.user_id == user_id)
    seen_ids: Set[int] = {row for row in session.exec(seen_stmt).all()}

    # Score aggregation: use rank-based scoring (higher rank = higher score)
    item_scores: Dict[int, float] = defaultdict(float)

    # Content-based scoring
    for rank, (item, _) in enumerate(content_items):
        if item.id is None or item.id in seen_ids:
            continue
        rank_score = 1.0 - (rank / max(len(content_items), 1))
        item_scores[item.id] += content_weight * rank_score

    # User-based scoring
    for rank, (item, _) in enumerate(user_items):
        if item.id is None or item.id in seen_ids:
            continue
        rank_score = 1.0 - (rank / max(len(user_items), 1))
        item_scores[item.id] += user_weight * rank_score

    if not item_scores:
        # Fallback: return content-based results if available
        return content_items[:k]

    # Sort by combined score
    sorted_items = sorted(item_scores.items(), key=lambda x: x[1], reverse=True)
    candidates = sorted_items[:k]
    top_item_ids = [item_id for item_id, _ in candidates]

    if not top_item_ids:
        return []

    # Fetch Item objects
    stmt = select(Item).where(col(Item.id).in_(top_item_ids))
    items = session.exec(stmt).all()

    # Preserve score order and return tuples
    item_map = {it.id: it for it in items}
    
    result = []
    for item_id, score in candidates:
        if item_id in item_map:
            result.append((item_map[item_id], score))
            
    return result
