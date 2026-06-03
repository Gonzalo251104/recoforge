import math
from datetime import datetime, UTC
from typing import Dict, List, Set, Tuple
from sqlmodel import Session, select

from app.core.utils import parse_tags_set
from app.db.models import Interaction, Item

def recommend_content_based(
    session: Session,
    user_id: int,
    k: int = 10,
    decay_factor: float = 0.05
) -> List[Tuple[Item, float]]:
    """
    Recommends items using TF-IDF weighting on tags.
    Builds a traveler profile vector from user interactions (weighted and decayed)
    and computes cosine similarity against candidate item tag vectors.
    """
    # 1. Fetch all items to compute Document Frequency (DF)
    all_items = session.exec(select(Item)).all()
    if not all_items:
        return []

    total_docs = len(all_items)
    tag_df: Dict[str, int] = {}
    item_tags_map: Dict[int, Set[str]] = {}

    for it in all_items:
        if it.id is None:
            continue
        tags = parse_tags_set(it.tags_json)
        item_tags_map[it.id] = tags
        for t in tags:
            tag_df[t] = tag_df.get(t, 0) + 1

    # Compute IDF for all tags: idf = ln(1 + N / (1 + df))
    tag_idf: Dict[str, float] = {}
    for tag, df in tag_df.items():
        tag_idf[tag] = math.log(1.0 + (total_docs / (1.0 + df)))

    # 2. Fetch user interactions to build profile vector
    interactions = session.exec(
        select(Interaction).where(Interaction.user_id == user_id)
    ).all()

    if not interactions:
        return []

    event_weights = {"view": 1.0, "click": 2.0, "save": 3.0}
    now = datetime.now(UTC)
    seen_ids: Set[int] = set()

    # User profile vector mapping tag -> score
    user_profile: Dict[str, float] = {}

    for inter in interactions:
        seen_ids.add(inter.item_id)
        if inter.item_id not in item_tags_map:
            continue

        weight = event_weights.get(inter.event_type.value if hasattr(inter.event_type, "value") else str(inter.event_type), 1.0)
        
        # Calculate temporal decay
        ts_utc = inter.ts
        if ts_utc.tzinfo is None:
            ts_utc = ts_utc.replace(tzinfo=UTC)
        
        days_diff = (now - ts_utc).total_seconds() / (3600.0 * 24.0)
        decay = math.exp(-decay_factor * max(0.0, days_diff))

        # Add tag weights to user profile
        for tag in item_tags_map[inter.item_id]:
            idf = tag_idf.get(tag, 1.0)
            user_profile[tag] = user_profile.get(tag, 0.0) + (weight * decay * idf)

    if not user_profile:
        return []

    # Calculate L2 norm of user profile vector
    profile_norm = math.sqrt(sum(val ** 2 for val in user_profile.values()))
    if profile_norm == 0.0:
        return []

    # 3. Calculate similarity score for unseen items
    scored_candidates: List[Tuple[Item, float]] = []

    for it in all_items:
        if it.id is None or it.id in seen_ids:
            continue

        tags = item_tags_map.get(it.id, set())
        if not tags:
            continue

        # Item vector: key = tag, value = idf
        # Dot product and item norm
        dot_product = 0.0
        item_squared_sum = 0.0

        for t in tags:
            idf = tag_idf.get(t, 1.0)
            item_squared_sum += idf ** 2
            if t in user_profile:
                dot_product += user_profile[t] * idf

        item_norm = math.sqrt(item_squared_sum)
        if item_norm == 0.0:
            continue

        # Cosine similarity
        score = dot_product / (profile_norm * item_norm)
        if score > 0.0:
            scored_candidates.append((it, score))

    # Sort candidates by score descending
    scored_candidates.sort(key=lambda x: x[1], reverse=True)
    return scored_candidates[:k]


def recommend_similar_items(
    session: Session,
    item_id: int,
    k: int = 10
) -> List[Tuple[Item, float]]:
    """
    Find items similar to a given item using cosine similarity on tag TF-IDF vectors.
    """
    all_items = session.exec(select(Item)).all()
    if not all_items:
        return []

    target_item = next((it for it in all_items if it.id == item_id), None)
    if not target_item:
        return []

    total_docs = len(all_items)
    tag_df: Dict[str, int] = {}
    item_tags_map: Dict[int, Set[str]] = {}

    for it in all_items:
        if it.id is None:
            continue
        tags = parse_tags_set(it.tags_json)
        item_tags_map[it.id] = tags
        for t in tags:
            tag_df[t] = tag_df.get(t, 0) + 1

    # Compute IDF for all tags
    tag_idf: Dict[str, float] = {}
    for tag, df in tag_df.items():
        tag_idf[tag] = math.log(1.0 + (total_docs / (1.0 + df)))

    target_tags = item_tags_map.get(item_id, set())
    if not target_tags:
        return []

    # Norm of target item
    target_squared_sum = 0.0
    for t in target_tags:
        idf = tag_idf.get(t, 1.0)
        target_squared_sum += idf ** 2
    target_norm = math.sqrt(target_squared_sum)
    if target_norm == 0.0:
        return []

    scored_candidates: List[Tuple[Item, float]] = []

    for it in all_items:
        if it.id is None or it.id == item_id:
            continue

        tags = item_tags_map.get(it.id, set())
        if not tags:
            continue

        dot_product = 0.0
        item_squared_sum = 0.0

        for t in tags:
            idf = tag_idf.get(t, 1.0)
            item_squared_sum += idf ** 2
            if t in target_tags:
                dot_product += idf * idf

        item_norm = math.sqrt(item_squared_sum)
        if item_norm == 0.0:
            continue

        score = dot_product / (target_norm * item_norm)
        if score > 0.0:
            scored_candidates.append((it, score))

    scored_candidates.sort(key=lambda x: x[1], reverse=True)
    return scored_candidates[:k]

