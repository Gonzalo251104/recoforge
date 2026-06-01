from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, col, func, select

from app.db.models import Item
from app.db.session import get_session
from app.core.utils import parse_tags
from app.api.schemas import ItemListResponse, ItemResponse

router = APIRouter(prefix="/items", tags=["items"])


@router.get("", response_model=ItemListResponse)
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

    # Base query for filtering
    base_stmt = select(Item)

    if q:
        base_stmt = base_stmt.where(col(Item.title).contains(q))
    if city:
        base_stmt = base_stmt.where(Item.city == city)
    if tag:
        # SQLite simple filter: substring match in tags_json
        base_stmt = base_stmt.where(col(Item.tags_json).contains(tag))

    # Count total matching items (single query)
    count_stmt = select(func.count()).select_from(base_stmt.subquery())
    total = session.exec(count_stmt).one()

    # Paginated query with OFFSET/LIMIT
    offset = (page - 1) * page_size
    paginated_stmt = base_stmt.offset(offset).limit(page_size)
    items = session.exec(paginated_stmt).all()

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
                "tags": parse_tags(it.tags_json),
            }
            for it in items
        ],
    }


@router.get("/{item_id}", response_model=ItemResponse)
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
        "tags": parse_tags(it.tags_json),
    }
