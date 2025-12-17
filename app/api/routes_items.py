import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db.models import Item
from app.db.session import get_session

router = APIRouter(prefix="/items", tags=["items"])


def _parse_tags(tags_json: str) -> List[str]:
    try:
        raw = json.loads(tags_json or "[]")
        if isinstance(raw, list):
            return [str(x) for x in raw]
    except Exception:
        pass
    return []


@router.get("")
def list_items(
    q: Optional[str] = None,
    city: Optional[str] = None,
    tag: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    session: Session = Depends(get_session),
):
    if page < 1:
        raise HTTPException(status_code=400, detail="page must be >= 1")
    if page_size < 1 or page_size > 100:
        raise HTTPException(status_code=400, detail="page_size must be between 1 and 100")

    stmt = select(Item)

    if q:
        stmt = stmt.where(Item.title.contains(q))
    if city:
        stmt = stmt.where(Item.city == city)
    if tag:
        # SQLite simple filter: substring match in tags_json
        stmt = stmt.where(Item.tags_json.contains(tag))

    items = session.exec(stmt).all()

    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    slice_items = items[start:end]

    return {
        "page": page,
        "pageSize": page_size,
        "total": total,
        "results": [
            {
                "id": it.id,
                "title": it.title,
                "city": it.city,
                "priceMin": it.price_min,
                "priceMax": it.price_max,
                "tags": _parse_tags(it.tags_json),
            }
            for it in slice_items
        ],
    }

@router.get("/{item_id}")
def get_item(item_id: int, session: Session = Depends(get_session)):
    it = session.get(Item, item_id)
    if it is None:
        raise HTTPException(status_code=404, detail="Item not found")

    return {
        "id": it.id,
        "title": it.title,
        "city": it.city,
        "priceMin": it.price_min,
        "priceMax": it.price_max,
        "tags": _parse_tags(it.tags_json),
    }
