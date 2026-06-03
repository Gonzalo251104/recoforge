import math
from datetime import datetime, UTC
from collections import defaultdict
from typing import List, Set, Tuple
from sqlmodel import Session, select

from app.db.models import Interaction, Item

def recommend_popular(
    session: Session,
    user_id: int | None = None,
    k: int = 10,
    decay_factor: float = 0.05
) -> List[Tuple[Item, float]]:
    """
    Recommends items based on their global popularity weighted by interaction types
    and discounted exponentially over time (temporal decay).
    Excludes items already seen by the user if user_id is provided.
    Returns list of tuples (Item, score).
    """
    event_weights = {"view": 1.0, "click": 2.0, "save": 3.0}
    now = datetime.now(UTC)

    # 1. Fetch seen item IDs for active user
    seen_ids: Set[int] = set()
    if user_id is not None:
        seen_stmt = select(Interaction.item_id).where(Interaction.user_id == user_id)
        seen_ids = set(session.exec(seen_stmt).all())

    # 2. Fetch all interactions to compute scores
    interactions = session.exec(select(Interaction)).all()
    item_scores: dict[int, float] = defaultdict(float)

    for inter in interactions:
        weight = event_weights.get(inter.event_type.value if hasattr(inter.event_type, "value") else str(inter.event_type), 1.0)
        
        # Calculate temporal decay
        ts_utc = inter.ts
        if ts_utc.tzinfo is None:
            ts_utc = ts_utc.replace(tzinfo=UTC)
        
        days_diff = (now - ts_utc).total_seconds() / (3600.0 * 24.0)
        decay = math.exp(-decay_factor * max(0.0, days_diff))
        
        item_scores[inter.item_id] += weight * decay

    # 3. Sort item IDs by score descending
    sorted_items = sorted(item_scores.items(), key=lambda x: x[1], reverse=True)
    
    # Filter seen items and select top-k candidates
    candidates = []
    for item_id, score in sorted_items:
        if item_id not in seen_ids:
            candidates.append((item_id, score))
        if len(candidates) >= k:
            break

    # If we don't have enough candidates from interactions, pad with remaining items
    if len(candidates) < k:
        candidate_ids = {cid for cid, _ in candidates}
        remaining_k = k - len(candidates)
        all_items = session.exec(select(Item)).all()
        for it in all_items:
            if it.id not in seen_ids and it.id not in candidate_ids:
                candidates.append((it.id, 0.0))
            if len(candidates) >= k:
                break

    # 4. Fetch Item objects and maintain sorting
    if not candidates:
        return []

    top_item_ids = [cid for cid, _ in candidates]
    stmt = select(Item).where(Item.id.in_(top_item_ids)) # type: ignore[attr-defined]
    db_items = session.exec(stmt).all()
    item_map = {it.id: it for it in db_items}

    result = []
    for item_id, score in candidates:
        if item_id in item_map:
            result.append((item_map[item_id], score))

    return result
