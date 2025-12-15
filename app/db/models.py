from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)


class Item(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    city: str = Field(index=True)
    price_min: float
    price_max: float
    # Storing tags as a JSON string (list) to simplify SQLite.
    tags_json: str = Field(default="[]")


class Interaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, foreign_key="user.id")
    item_id: int = Field(index=True, foreign_key="item.id")
    event_type: str = Field(index=True)  # view | click | save
    ts: datetime = Field(default_factory=datetime.utcnow, index=True)
    