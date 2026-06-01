from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, desc, select

from app.db.models import Interaction, Item, User
from app.db.session import get_session
from app.core.utils import parse_tags
from app.api.schemas import UserHistoryResponse, HistoryEntryResponse, HistoryItemResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/{user_id}/history", response_model=UserHistoryResponse)
def get_user_history(
    user_id: int, limit: int = 50, session: Session = Depends(get_session)
) -> UserHistoryResponse:
    if limit <= 0 or limit > 200:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 200")

    user = session.exec(select(User).where(User.id == user_id)).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    stmt = (
        select(Interaction, Item)
        .join(Item)
        .where(Interaction.user_id == user_id)
        .order_by(desc(Interaction.ts))
        .limit(limit)
    )

    rows = session.exec(stmt).all()

    return UserHistoryResponse(
        userId=user_id,
        limit=limit,
        results=[
            HistoryEntryResponse(
                eventId=ev.id if ev.id is not None else 0,
                eventType=ev.event_type,
                ts=ev.ts.isoformat() if ev.ts else None,
                item=HistoryItemResponse(
                    id=it.id if it.id is not None else 0,
                    title=it.title,
                    city=it.city,
                    priceMin=it.price_min,
                    priceMax=it.price_max,
                    tags=parse_tags(it.tags_json),
                ),
            )
            for ev, it in rows
        ],
    )
