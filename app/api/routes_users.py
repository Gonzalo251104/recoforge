from collections import Counter
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, desc, func, select

from app.db.models import Interaction, Item, User, InteractionType
from app.db.session import get_session
from app.core.utils import parse_tags
from app.api.schemas import (
    UserHistoryResponse,
    HistoryEntryResponse,
    HistoryItemResponse,
    UserListResponse,
    UserResponse,
    CreateUserRequest,
    UserProfileResponse,
    UserStats,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=UserListResponse)
def list_users(
    page: int = 1, page_size: int = 20, session: Session = Depends(get_session)
) -> UserListResponse:
    if page < 1:
        raise HTTPException(status_code=400, detail="page must be >= 1")
    if page_size < 1 or page_size > 100:
        raise HTTPException(status_code=400, detail="page_size must be between 1 and 100")

    offset = (page - 1) * page_size
    total = session.exec(select(func.count(User.id))).one()

    users = session.exec(
        select(User).order_by(User.username).offset(offset).limit(page_size)
    ).all()

    return UserListResponse(
        page=page,
        pageSize=page_size,
        total=total,
        results=[
            UserResponse(
                id=u.id if u.id is not None else 0,
                username=u.username,
                created_at=u.created_at.isoformat() if u.created_at else "",
            )
            for u in users
        ],
    )


@router.post("", response_model=UserResponse, status_code=201)
def create_user(
    payload: CreateUserRequest, session: Session = Depends(get_session)
) -> UserResponse:
    # Check if username exists
    existing = session.exec(select(User).where(User.username == payload.username)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    user = User(username=payload.username)
    session.add(user)
    session.commit()
    session.refresh(user)

    return UserResponse(
        id=user.id if user.id is not None else 0,
        username=user.username,
        created_at=user.created_at.isoformat() if user.created_at else "",
    )


@router.get("/{user_id}", response_model=UserProfileResponse)
def get_user_profile(
    user_id: int, session: Session = Depends(get_session)
) -> UserProfileResponse:
    user = session.exec(select(User).where(User.id == user_id)).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Calculate statistics from interactions
    interactions = session.exec(
        select(Interaction, Item)
        .join(Item)
        .where(Interaction.user_id == user_id)
    ).all()

    views = 0
    clicks = 0
    saves = 0
    tags_list = []

    for ev, it in interactions:
        if ev.event_type == InteractionType.VIEW:
            views += 1
        elif ev.event_type == InteractionType.CLICK:
            clicks += 1
        elif ev.event_type == InteractionType.SAVE:
            saves += 1

        tags_list.extend(parse_tags(it.tags_json))

    # Top 5 tags
    top_tags = [tag for tag, _ in Counter(tags_list).most_common(5)]

    return UserProfileResponse(
        id=user_id,
        username=user.username,
        created_at=user.created_at.isoformat() if user.created_at else "",
        stats=UserStats(
            totalViews=views,
            totalClicks=clicks,
            totalSaves=saves,
            favoriteTags=top_tags,
        ),
    )


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
