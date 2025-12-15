import random
from datetime import datetime, timedelta

from sqlmodel import Session, SQLModel, select

from app.db.models import Interaction, Item, User
from app.db.session import engine
from app.data.datasets import make_items


EVENT_TYPES = ["view", "click", "save"]


def reset_db():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


def seed(users_n: int = 30, items_n: int = 120, interactions_n: int = 800):
    reset_db()

    with Session(engine) as session:
        # Users
        users = [User(username=f"user{i+1:03d}") for i in range(users_n)]
        session.add_all(users)
        session.commit()

        users = session.exec(select(User)).all()

        # Items
        items_seed = make_items(items_n)
        items = [
            Item(
                title=it.title,
                city=it.city,
                price_min=it.price_min,
                price_max=it.price_max,
                tags_json=it.tags_json(),
            )
            for it in items_seed
        ]
        session.add_all(items)
        session.commit()

        items = session.exec(select(Item)).all()

        # Interactions
        now = datetime.utcnow()
        rows = []
        for _ in range(interactions_n):
            u = random.choice(users)
            it = random.choice(items)
            et = random.choices(EVENT_TYPES, weights=[0.72, 0.22, 0.06])[0]
            ts = now - timedelta(days=random.randint(0, 30), minutes=random.randint(0, 60 * 24))
            rows.append(Interaction(user_id=u.id, item_id=it.id, event_type=et, ts=ts))

        session.add_all(rows)
        session.commit()

    print(f"Seed OK users={users_n}, items={items_n}, interactions={interactions_n}")


if __name__ == "__main__":
    seed()
