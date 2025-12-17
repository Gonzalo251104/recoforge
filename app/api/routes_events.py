from datetime import datetime, UTC
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db.models import Interaction, Item, User
from app.db.session import get_session

router = APIRouter(prefix="/events", tags=["events"])


class CreateEventRequest(BaseModel):
    userId: int = Field(..., ge=1)
    itemId: int = Field(..., ge=1)
    eventType: str = Field(..., pattern="^(view|click|save)$")


@router.post("")
def create_event(payload: CreateEventRequest, session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.id == payload.userId)).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    item = session.exec(select(Item).where(Item.id == payload.itemId)).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")

    ev = Interaction(
        user_id=payload.userId,
        item_id=payload.itemId,
        event_type=payload.eventType,
        ts=datetime.now(UTC),
    )
    session.add(ev)
    session.commit()
    session.refresh(ev)

    return {
        "id": ev.id,
        "userId": ev.user_id,
        "itemId": ev.item_id,
        "eventType": ev.event_type,
        "ts": ev.ts.isoformat(),
    }
