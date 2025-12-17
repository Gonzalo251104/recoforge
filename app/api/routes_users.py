from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db.models import Interaction, Item, User
from app.db.session import get_session

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/{user_id}/history")
def get_user_history(user_id: int, limit: int = 50, session: Session = Depends(get_session)):
    if limit <= 0 or limit > 200:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 200")

    user = session.exec(select(User).where(User.id == user_id)).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    stmt = (
        select(Interaction, Item)
        .join(Item, Item.id == Interaction.item_id)
        .where(Interaction.user_id == user_id)
        .order_by(Interaction.ts.desc())
        .limit(limit)
    )

    rows = session.exec(stmt).all()

    return {
        "userId": user_id,
        "limit": limit,
        "results": [
            {
                "eventId": ev.id,
                "eventType": ev.event_type,
                "ts": ev.ts.isoformat() if ev.ts else None,
                "item": {
                    "id": it.id,
                    "title": it.title,
                    "city": it.city,
                    "priceMin": it.price_min,
                    "priceMax": it.price_max,
                    "tagsJson": it.tags_json,
                },
            }
            for ev, it in rows
        ],
    }
