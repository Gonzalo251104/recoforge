"""Shared utility functions."""

import json
from typing import List, Set


def parse_tags(tags_json: str) -> List[str]:
    """Parse tags from JSON string to list of strings."""
    try:
        raw = json.loads(tags_json or "[]")
        if isinstance(raw, list):
            return [str(x) for x in raw]
    except (json.JSONDecodeError, TypeError):
        pass
    return []


def parse_tags_set(tags_json: str) -> Set[str]:
    """Parse tags from JSON string to set of normalized (lowercase, stripped) strings."""
    try:
        raw = json.loads(tags_json or "[]")
        if isinstance(raw, list):
            return {str(x).strip().lower() for x in raw if str(x).strip()}
    except (json.JSONDecodeError, TypeError):
        pass
    return set()
