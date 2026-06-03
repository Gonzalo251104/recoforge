from datetime import datetime, UTC
from enum import Enum
from typing import List, Optional

from sqlmodel import Field, Relationship, SQLModel


class InteractionType(str, Enum):
    VIEW = "view"
    CLICK = "click"
    SAVE = "save"


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    interactions: List["Interaction"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class Item(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: str = Field(default="")
    city: str = Field(index=True)
    price_min: float
    price_max: float
    tags_json: str = Field(default="[]")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    interactions: List["Interaction"] = Relationship(
        back_populates="item",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class Interaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, foreign_key="user.id")
    item_id: int = Field(index=True, foreign_key="item.id")
    event_type: InteractionType = Field(index=True)
    ts: datetime = Field(default_factory=lambda: datetime.now(UTC), index=True)

    user: User = Relationship(back_populates="interactions")
    item: Item = Relationship(back_populates="interactions")