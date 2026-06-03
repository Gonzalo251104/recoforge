from datetime import datetime, UTC
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, desc, func, select

from app.api.schemas import CreateEventRequest, EventResponse, EventListResponse, EventListEntry
from app.db.models import Interaction, Item, User, InteractionType
from app.db.session import get_session

router = APIRouter(prefix="/events", tags=["events"])


@router.post("", response_model=EventResponse)
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
        event_type=InteractionType(payload.eventType),
        ts=datetime.now(UTC),
    )
    session.add(ev)
    session.commit()
    session.refresh(ev)

    return {
        "id": ev.id,
        "userId": ev.user_id,
        "itemId": ev.item_id,
        "eventType": ev.event_type.value,
        "ts": ev.ts.isoformat(),
    }


@router.get("", response_model=EventListResponse)
def list_events(
    user_id: Optional[int] = None,
    item_id: Optional[int] = None,
    event_type: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    session: Session = Depends(get_session),
) -> EventListResponse:
    if page < 1:
        raise HTTPException(status_code=400, detail="page must be >= 1")
    if page_size < 1 or page_size > 100:
        raise HTTPException(status_code=400, detail="page_size must be between 1 and 100")

    offset = (page - 1) * page_size

    stmt = select(Interaction, Item).join(Item)
    count_stmt = select(func.count(Interaction.id))

    if user_id:
        stmt = stmt.where(Interaction.user_id == user_id)
        count_stmt = count_stmt.where(Interaction.user_id == user_id)
    if item_id:
        stmt = stmt.where(Interaction.item_id == item_id)
        count_stmt = count_stmt.where(Interaction.item_id == item_id)
    if event_type:
        stmt = stmt.where(Interaction.event_type == event_type)
        count_stmt = count_stmt.where(Interaction.event_type == event_type)

    total = session.exec(count_stmt).one()

    stmt = stmt.order_by(desc(Interaction.ts)).offset(offset).limit(page_size)
    rows = session.exec(stmt).all()

    return EventListResponse(
        page=page,
        pageSize=page_size,
        total=total,
        results=[
            EventListEntry(
                id=ev.id if ev.id is not None else 0,
                userId=ev.user_id,
                itemId=ev.item_id,
                eventType=ev.event_type.value if hasattr(ev.event_type, "value") else str(ev.event_type),
                ts=ev.ts.isoformat() if ev.ts else "",
                itemTitle=it.title,
                itemCity=it.city,
            )
            for ev, it in rows
        ],
    )
