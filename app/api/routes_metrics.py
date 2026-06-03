"""Offline evaluation metrics endpoint."""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.db.session import get_session
from app.reco.metrics import evaluate_offline

router = APIRouter(prefix="/metrics", tags=["metrics"])

SUPPORTED_STRATEGIES = {"content", "user", "hybrid", "popular"}


@router.get("/offline")
def offline_metrics(
    strategy: str = "content",
    k: int = 10,
    users: int = 20,
    session: Session = Depends(get_session),
):
    """Run offline evaluation for a recommendation strategy."""
    if k <= 0 or k > 100:
        raise HTTPException(status_code=400, detail="k must be between 1 and 100")
    if users <= 0 or users > 200:
        raise HTTPException(status_code=400, detail="users must be between 1 and 200")
    if strategy not in SUPPORTED_STRATEGIES:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown strategy '{strategy}'. Supported: {', '.join(sorted(SUPPORTED_STRATEGIES))}",
        )

    return evaluate_offline(session=session, strategy=strategy, k=k, users_limit=users)


@router.get("/offline/all")
def offline_metrics_all(
    k: int = 10,
    users: int = 20,
    session: Session = Depends(get_session),
):
    """Run offline evaluation for all recommendation strategies."""
    if k <= 0 or k > 100:
        raise HTTPException(status_code=400, detail="k must be between 1 and 100")
    if users <= 0 or users > 200:
        raise HTTPException(status_code=400, detail="users must be between 1 and 200")

    results = {}
    for strategy in sorted(SUPPORTED_STRATEGIES):
        results[strategy] = evaluate_offline(
            session=session, strategy=strategy, k=k, users_limit=users
        )
    return results
