import json
import random
from dataclasses import dataclass
from typing import List


CITIES = ["Lima", "Arequipa", "Cusco", "Trujillo", "Piura"]
TAGS = [
    "rock", "kpop", "anime", "tech", "food", "sports", "indie",
    "jazz", "latin", "pop", "gaming", "startup"
]


@dataclass(frozen=True)
class SeedItem:
    title: str
    city: str
    price_min: float
    price_max: float
    tags: List[str]

    def tags_json(self) -> str:
        return json.dumps(self.tags, ensure_ascii=False)


def make_items(n: int) -> List[SeedItem]:
    items: List[SeedItem] = []
    for i in range(n):
        city = random.choice(CITIES)
        tags = random.sample(TAGS, k=random.randint(2, 5))
        p1 = round(random.uniform(10, 80), 2)
        p2 = round(p1 + random.uniform(5, 120), 2)
        items.append(
            SeedItem(
                title=f"Event #{i+1} - {random.choice(['Live', 'Fest', 'Night', 'Show'])}",
                city=city,
                price_min=p1,
                price_max=p2,
                tags=tags,
            )
        )
    return items
