import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.main import app
from app.db.session import get_session
from app.db.models import Interaction, Item, User


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    SQLModel.metadata.create_all(engine)

    def override_get_session():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    with Session(engine) as session:
        u1 = User(username="user001")
        u2 = User(username="user002")
        session.add_all([u1, u2])
        session.commit()
        session.refresh(u1)
        session.refresh(u2)

        i1 = Item(
            title="Event 1",
            city="Lima",
            price_min=10.0,
            price_max=20.0,
            tags_json='["rock","indie"]',
        )
        i2 = Item(
            title="Event 2",
            city="Lima",
            price_min=15.0,
            price_max=30.0,
            tags_json='["rock","pop"]',
        )
        i3 = Item(
            title="Event 3",
            city="Cusco",
            price_min=12.0,
            price_max=25.0,
            tags_json='["kpop","pop"]',
        )
        session.add_all([i1, i2, i3])
        session.commit()
        session.refresh(i1)
        session.refresh(i2)
        session.refresh(i3)

        session.add_all(
            [
                Interaction(user_id=u1.id, item_id=i1.id, event_type="view"),
                Interaction(user_id=u1.id, item_id=i2.id, event_type="save"),
            ]
        )
        session.commit()

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
