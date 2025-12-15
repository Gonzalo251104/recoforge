from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.db.session import get_session
from app.reco.content_based import recommend_content_based

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/{user_id}")
def get_recommendations(
    user_id: int,
    strategy: str = "content",
    k: int = 10,
    session: Session = Depends(get_session),
):
    if k <= 0 or k > 100:
        raise HTTPException(status_code=400, detail="k must be between 1 and 100")

    if strategy != "content":
        raise HTTPException(status_code=400, detail="Only strategy=content is available for now")

    items = recommend_content_based(session=session, user_id=user_id, k=k)
    return {
        "userId": user_id,
        "strategy": strategy,
        "k": k,
        "results": [
            {
                "id": it.id,
                "title": it.title,
                "city": it.city,
                "priceMin": it.price_min,
                "priceMax": it.price_max,
                "tagsJson": it.tags_json,
            }
            for it in items
        ],
    }
