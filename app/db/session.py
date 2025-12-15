from sqlmodel import Session, create_engine

DB_URL = "sqlite:///./recoforge.db"

engine = create_engine(
    DB_URL,
    echo=False,
    connect_args={"check_same_thread": False},  # SQLite + FastAPI
)


def get_session():
    with Session(engine) as session:
        yield session
