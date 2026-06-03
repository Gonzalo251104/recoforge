import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, col, func, select

from app.db.models import Item
from app.db.session import get_session
from app.core.utils import parse_tags, parse_tags_set
from app.api.schemas import (
    ItemListResponse,
    ItemResponse,
    CreateItemRequest,
    UpdateItemRequest,
    RecommendedItemResponse,
)
from app.reco.content_based import recommend_similar_items

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
                "description": it.description,
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
        "description": it.description,
        "city": it.city,
        "priceMin": it.price_min,
        "priceMax": it.price_max,
        "tags": parse_tags(it.tags_json),
    }


@router.post("", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
def create_item(payload: CreateItemRequest, session: Session = Depends(get_session)):
    it = Item(
        title=payload.title,
        description=payload.description,
        city=payload.city,
        price_min=payload.priceMin,
        price_max=payload.priceMax,
        tags_json=json.dumps(payload.tags),
    )
    session.add(it)
    session.commit()
    session.refresh(it)
    return {
        "id": it.id,
        "title": it.title,
        "description": it.description,
        "city": it.city,
        "priceMin": it.price_min,
        "priceMax": it.price_max,
        "tags": payload.tags,
    }


@router.put("/{item_id}", response_model=ItemResponse)
def update_item(item_id: int, payload: UpdateItemRequest, session: Session = Depends(get_session)):
    it = session.get(Item, item_id)
    if it is None:
        raise HTTPException(status_code=404, detail="Item not found")

    if payload.title is not None:
        it.title = payload.title
    if payload.description is not None:
        it.description = payload.description
    if payload.city is not None:
        it.city = payload.city
    if payload.priceMin is not None:
        it.price_min = payload.priceMin
    if payload.priceMax is not None:
        it.price_max = payload.priceMax
    if payload.tags is not None:
        it.tags_json = json.dumps(payload.tags)

    session.add(it)
    session.commit()
    session.refresh(it)

    return {
        "id": it.id,
        "title": it.title,
        "description": it.description,
        "city": it.city,
        "priceMin": it.price_min,
        "priceMax": it.price_max,
        "tags": parse_tags(it.tags_json),
    }


@router.delete("/{item_id}")
def delete_item(item_id: int, session: Session = Depends(get_session)):
    it = session.get(Item, item_id)
    if it is None:
        raise HTTPException(status_code=404, detail="Item not found")

    session.delete(it)
    session.commit()
    return {"status": "success", "message": f"Item {item_id} deleted"}


@router.get("/{item_id}/similar", response_model=List[RecommendedItemResponse])
def get_similar_items(
    item_id: int,
    k: int = Query(5, ge=1, le=100),
    session: Session = Depends(get_session),
):
    it = session.get(Item, item_id)
    if it is None:
        raise HTTPException(status_code=404, detail="Item not found")

    similar_with_scores = recommend_similar_items(session, item_id, k=k)
    target_tags = parse_tags_set(it.tags_json)

    results = []
    for candidate, score in similar_with_scores:
        if candidate.id is None:
            continue
        candidate_tags = parse_tags_set(candidate.tags_json)
        common_tags = target_tags.intersection(candidate_tags)

        # Build explanation
        score_val = round(float(score), 4)
        if common_tags:
            tag_list_str = ", ".join(sorted(list(common_tags))[:3])
            explanation = f"Similar destination in {candidate.city} sharing interests: {tag_list_str}."
        else:
            explanation = f"Top alternative destination in {candidate.city} with comparable attributes."

        results.append(
            RecommendedItemResponse(
                id=candidate.id,
                title=candidate.title,
                description=candidate.description,
                city=candidate.city,
                priceMin=candidate.price_min,
                priceMax=candidate.price_max,
                tags=parse_tags(candidate.tags_json),
                score=score_val,
                explanation=explanation,
            )
        )
    return results
