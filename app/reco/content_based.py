import json
from typing import Iterable, List, Set, Tuple

from sqlmodel import Session, select

from app.db.models import Interaction, Item


def _jaccard(a: Set[str], b: Set[str]) -> float:
    if not a and not b:
        return 0.0
    inter = len(a.intersection(b))
    union = len(a.union(b))
    return inter / union if union else 0.0


def _parse_tags(tags_json: str) -> Set[str]:
    try:
        raw = json.loads(tags_json or "[]")
        if isinstance(raw, list):
            return {str(x).strip().lower() for x in raw if str(x).strip()}
    except Exception:
        pass
    return set()


def _user_profile_tags(session: Session, user_id: int, limit_history: int = 1000) -> Set[str]:
    """
    Builds a simple user profile as the union of tags from items the user interacted with.
    We weight interactions implicitly by including items from history (you can refine later).
    """
    stmt = (
        select(Interaction, Item)
        .join(Item, Item.id == Interaction.item_id)
        .where(Interaction.user_id == user_id)
        .order_by(Interaction.ts.desc())
        .limit(limit_history)
    )
    rows: Iterable[Tuple[Interaction, Item]] = session.exec(stmt).all()

    profile: Set[str] = set()
    for _, item in rows:
        profile |= _parse_tags(item.tags_json)
    return profile


def recommend_content_based(session: Session, user_id: int, k: int = 10) -> List[Item]:
    """
    Recommends items by comparing each candidate item's tags to the user's profile tags.
    Returns top-k items not yet interacted with by the user.
    """
    profile = _user_profile_tags(session, user_id=user_id)
    if not profile:
        return []

    seen_stmt = select(Interaction.item_id).where(Interaction.user_id == user_id)
    seen_ids = {row for row in session.exec(seen_stmt).all()}

    items = session.exec(select(Item)).all()

    scored: List[Tuple[float, Item]] = []
    for it in items:
        if it.id in seen_ids:
            continue
        tags = _parse_tags(it.tags_json)
        score = _jaccard(profile, tags)
        if score > 0:
            scored.append((score, it))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [it for _, it in scored[: max(0, k)]]
