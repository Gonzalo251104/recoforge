from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.db.session import get_session
from app.reco.metrics import evaluate_content_based

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/offline")
def offline_metrics(
    strategy: str = "content",
    k: int = 10,
    users: int = 20,
    session: Session = Depends(get_session),
):
    if k <= 0 or k > 100:
        raise HTTPException(status_code=400, detail="k must be between 1 and 100")
    if users <= 0 or users > 200:
        raise HTTPException(status_code=400, detail="users must be between 1 and 200")

    if strategy != "content":
        raise HTTPException(
            status_code=400, detail="Only strategy=content is available for now"
        )

    scores = evaluate_content_based(session=session, k=k, users_limit=users)

    return {
        "strategy": strategy,
        "k": k,
        "usersEvaluated": users,
        "metrics": scores,
    }
