"""Offline evaluation metrics with proper train/test split.

Implements temporal split: the most recent interactions per user are held out
as the test set, and recommendations are generated using only training data.
"""

from math import log2
from typing import Any, Dict, List, Set

from sqlmodel import Session, asc, select

from app.db.models import Interaction, User
from app.reco.content_based import recommend_content_based
from app.reco.user_based import recommend_user_based
from app.reco.hybrid import recommend_hybrid

STRATEGY_MAP = {
    "content": recommend_content_based,
    "user": recommend_user_based,
    "hybrid": recommend_hybrid,
}


def precision_at_k(recommended: List[int], relevant: Set[int], k: int) -> float:
    """Compute precision@k: fraction of top-k recommendations that are relevant."""
    if k <= 0:
        return 0.0
    rec_k = recommended[:k]
    if not rec_k:
        return 0.0
    hits = sum(1 for item_id in rec_k if item_id in relevant)
    return hits / float(k)


def recall_at_k(recommended: List[int], relevant: Set[int], k: int) -> float:
    """Compute recall@k: fraction of relevant items found in top-k recommendations."""
    if not relevant:
        return 0.0
    rec_k = recommended[:k]
    hits = sum(1 for item_id in rec_k if item_id in relevant)
    return hits / float(len(relevant))


def ndcg_at_k(recommended: List[int], relevant: Set[int], k: int) -> float:
    """Compute NDCG@k: normalized discounted cumulative gain."""
    if k <= 0 or not relevant:
        return 0.0
    rec_k = recommended[:k]
    dcg = sum(
        (1.0 / log2(i + 2)) for i, item_id in enumerate(rec_k) if item_id in relevant
    )
    ideal_hits = min(len(relevant), k)
    idcg = sum(1.0 / log2(i + 2) for i in range(ideal_hits))
    return dcg / idcg if idcg > 0 else 0.0


def _temporal_split(
    session: Session, user_id: int, test_fraction: float = 0.2
) -> tuple[Set[int], Set[int]]:
    """Split a user's interactions into train and test sets based on timestamp.

    The most recent ``test_fraction`` of interactions form the test set.

    Returns:
        A tuple of (train_item_ids, test_item_ids).
    """
    stmt = (
        select(Interaction.item_id)
        .where(Interaction.user_id == user_id)
        .order_by(asc(Interaction.ts))
    )
    all_item_ids = list(session.exec(stmt).all())

    if len(all_item_ids) < 3:
        return set(all_item_ids), set()

    split_idx = max(1, int(len(all_item_ids) * (1 - test_fraction)))
    train_ids = set(all_item_ids[:split_idx])
    test_ids = set(all_item_ids[split_idx:])
    return train_ids, test_ids


def evaluate_offline(
    session: Session,
    strategy: str = "content",
    k: int = 10,
    users_limit: int = 20,
) -> Dict[str, Any]:
    """Evaluate a recommendation strategy using temporal train/test split.

    For each user, the most recent 20% of interactions are held out as the
    test set. Recommendations are generated and evaluated against this test set.

    Returns:
        A dict with strategy, k, usersEvaluated, and average metrics.
    """
    strat_fn = STRATEGY_MAP.get(strategy)
    if strat_fn is None:
        return {
            "strategy": strategy,
            "k": k,
            "usersEvaluated": 0,
            "metrics": {"precision@k": 0.0, "recall@k": 0.0, "ndcg@k": 0.0},
        }

    users = session.exec(select(User).limit(users_limit)).all()

    precisions: List[float] = []
    recalls: List[float] = []
    ndcgs: List[float] = []

    for user in users:
        if user.id is None:
            continue

        _train_ids, test_ids = _temporal_split(session, user.id)

        if not test_ids:
            continue

        items = strat_fn(session=session, user_id=user.id, k=k)
        recommended_ids = [it.id for it in items if it.id is not None]

        precisions.append(precision_at_k(recommended_ids, test_ids, k))
        recalls.append(recall_at_k(recommended_ids, test_ids, k))
        ndcgs.append(ndcg_at_k(recommended_ids, test_ids, k))

    evaluated = len(precisions)
    avg_p = sum(precisions) / evaluated if evaluated > 0 else 0.0
    avg_r = sum(recalls) / evaluated if evaluated > 0 else 0.0
    avg_n = sum(ndcgs) / evaluated if evaluated > 0 else 0.0

    return {
        "strategy": strategy,
        "k": k,
        "usersEvaluated": evaluated,
        "metrics": {
            "precision@k": round(avg_p, 4),
            "recall@k": round(avg_r, 4),
            "ndcg@k": round(avg_n, 4),
        },
    }
