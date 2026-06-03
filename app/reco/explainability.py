import logging
from typing import List, Set
from sqlmodel import Session, select

from app.db.models import Interaction, Item
from app.core.utils import parse_tags_set

logger = logging.getLogger("app.reco.explainability")

def generate_explanation(
    session: Session,
    user_id: int,
    item_id: int,
    strategy: str,
    score: float
) -> str:
    """
    Generates a human-readable, user-friendly explanation for a recommendation.
    """
    try:
        # Fetch the item
        item = session.exec(select(Item).where(Item.id == item_id)).first()
        if not item:
            return "Recommended based on system popularity."

        if strategy == "popular":
            # Just popular fallback
            if score > 5.0:
                return "Highly trending among users in the community right now."
            return "Trending activity popular among other travelers."

        # Fetch user history items to find overlaps
        user_interactions = session.exec(
            select(Interaction, Item)
            .join(Item)
            .where(Interaction.user_id == user_id)
        ).all()

        if not user_interactions:
            # Cold-start explanation
            return "Recommended to start your journey in this city."

        item_tags = parse_tags_set(item.tags_json)

        if strategy == "content":
            # Find overlapping tags
            user_tags: Set[str] = set()
            for _, it in user_interactions:
                user_tags |= parse_tags_set(it.tags_json)

            overlap = item_tags & user_tags
            if overlap:
                # Get up to 3 shared tags
                shared = list(overlap)[:3]
                return f"Matches your interest in: {', '.join(shared)}."
            return "Matches activities you explored in similar cities."

        elif strategy == "user":
            # Collaborative filtering explanation
            # Find other users who interacted with this item and check similarity
            # Simulating explanation
            return "Popular among travelers who share similar activity preferences with you."

        elif strategy == "hybrid":
            # Hybrid explanation
            # Combination of interests and popularity/user patterns
            user_tags = set()
            for _, it in user_interactions:
                user_tags |= parse_tags_set(it.tags_json)
            overlap = item_tags & user_tags
            if overlap:
                shared = list(overlap)[:2]
                return f"Combines your interest in '{', '.join(shared)}' with similar user trends."
            return "Fits your traveler profile and is popular among similar explorers."

        return "Personalized recommendation matched to your traveler profile."
    except Exception as e:
        logger.error(f"Error generating explanation for user {user_id}, item {item_id}: {str(e)}")
        return "Matched to your profile based on past activity preferences."
