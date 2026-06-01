"""User-based collaborative filtering recommendation engine.

This module implements user-based collaborative filtering using cosine similarity
between user interaction vectors.
"""

from collections import defaultdict
from math import sqrt
from typing import Dict, List, Set, Tuple

from sqlmodel import Session, col, select

from app.db.models import Interaction, Item


def _get_user_interactions(session: Session) -> Dict[int, Dict[int, float]]:
    """
    Build a dictionary mapping user_id -> {item_id: score}.
    Scores are based on interaction types: view=1, click=2, save=3.
    """
    event_weights = {"view": 1.0, "click": 2.0, "save": 3.0}

    stmt = select(Interaction)
    interactions = session.exec(stmt).all()

    user_items: Dict[int, Dict[int, float]] = defaultdict(lambda: defaultdict(float))

    for inter in interactions:
        weight = event_weights.get(inter.event_type, 1.0)
        user_items[inter.user_id][inter.item_id] += weight

    return {uid: dict(items) for uid, items in user_items.items()}


def _cosine_similarity(vec_a: Dict[int, float], vec_b: Dict[int, float]) -> float:
    """Calculate cosine similarity between two sparse vectors."""
    if not vec_a or not vec_b:
        return 0.0

    common_keys = set(vec_a.keys()) & set(vec_b.keys())
    if not common_keys:
        return 0.0

    dot_product = sum(vec_a[k] * vec_b[k] for k in common_keys)
    norm_a = sqrt(sum(v ** 2 for v in vec_a.values()))
    norm_b = sqrt(sum(v ** 2 for v in vec_b.values()))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot_product / (norm_a * norm_b)


def _find_similar_users(
    target_user_id: int,
    user_interactions: Dict[int, Dict[int, float]],
    top_n: int = 10,
) -> List[Tuple[int, float]]:
    """Find the top-N most similar users to the target user."""
    target_vec = user_interactions.get(target_user_id, {})
    if not target_vec:
        return []

    similarities: List[Tuple[int, float]] = []

    for other_user_id, other_vec in user_interactions.items():
        if other_user_id == target_user_id:
            continue
        sim = _cosine_similarity(target_vec, other_vec)
        if sim > 0:
            similarities.append((other_user_id, sim))

    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities[:top_n]


def recommend_user_based(
    session: Session,
    user_id: int,
    k: int = 10,
    num_similar_users: int = 10,
) -> List[Item]:
    """
    Recommend items using user-based collaborative filtering.

    1. Find users similar to the target user (based on interaction patterns).
    2. Aggregate items those similar users liked but target hasn't seen.
    3. Rank by weighted similarity scores.
    """
    user_interactions = _get_user_interactions(session)

    # Items the target user has already interacted with
    seen_items: Set[int] = set(user_interactions.get(user_id, {}).keys())

    # Find similar users
    similar_users = _find_similar_users(user_id, user_interactions, num_similar_users)

    if not similar_users:
        return []

    # Aggregate scores for unseen items
    item_scores: Dict[int, float] = defaultdict(float)

    for other_user_id, similarity in similar_users:
        other_items = user_interactions.get(other_user_id, {})
        for item_id, score in other_items.items():
            if item_id not in seen_items:
                # Weight the item score by user similarity
                item_scores[item_id] += similarity * score

    if not item_scores:
        return []

    # Sort by score descending
    sorted_items = sorted(item_scores.items(), key=lambda x: x[1], reverse=True)
    top_item_ids = [item_id for item_id, _ in sorted_items[:k]]

    # Fetch Item objects
    if not top_item_ids:
        return []

    stmt = select(Item).where(col(Item.id).in_(top_item_ids))
    items = session.exec(stmt).all()

    # Preserve score order
    item_map = {it.id: it for it in items}
    return [item_map[iid] for iid in top_item_ids if iid in item_map]
