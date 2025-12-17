from typing import Dict, Iterable, List, Set, Tuple

from sqlmodel import Session, select

from app.db.models import Interaction, Item, User
from app.reco.content_based import recommend_content_based


def _user_relevant_items(
    session: Session, user_id: int, min_event: str = "save"
) -> Set[int]:
    """
    Defines relevant items for a user.
    By default, considers items with 'save' interactions as relevant.
    """
    stmt = select(Interaction.item_id).where(
        Interaction.user_id == user_id,
        Interaction.event_type == min_event,
    )
    return {row for row in session.exec(stmt).all()}


def precision_at_k(recommended: List[int], relevant: Set[int], k: int) -> float:
    if k <= 0:
        return 0.0
    rec_k = recommended[:k]
    if not rec_k:
        return 0.0
    hits = sum(1 for it in rec_k if it in relevant)
    return hits / float(k)


def recall_at_k(recommended: List[int], relevant: Set[int], k: int) -> float:
    if not relevant:
        return 0.0
    rec_k = recommended[:k]
    hits = sum(1 for it in rec_k if it in relevant)
    return hits / float(len(relevant))


def evaluate_content_based(
    session: Session, k: int = 10, users_limit: int = 20
) -> Dict[str, float]:
    """
    Evaluates content-based recommendations over a subset of users.
    """
    users = session.exec(select(User).limit(users_limit)).all()

    precisions: List[float] = []
    recalls: List[float] = []

    for u in users:
        relevant = _user_relevant_items(session, u.id)
        if not relevant:
            continue

        items = recommend_content_based(session, u.id, k=k)
        recommended_ids = [it.id for it in items]

        precisions.append(precision_at_k(recommended_ids, relevant, k))
        recalls.append(recall_at_k(recommended_ids, relevant, k))

    if not precisions:
        return {"precision@k": 0.0, "recall@k": 0.0}

    return {
        "precision@k": round(sum(precisions) / len(precisions), 4),
        "recall@k": round(sum(recalls) / len(recalls), 4),
    }
