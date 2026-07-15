from sqlalchemy import create_engine
from sqlalchemy.engine import URL, Engine, make_url
from sqlalchemy.orm import Session, sessionmaker


def build_sqlalchemy_url(database_url: str) -> URL:
    if not database_url.strip():
        raise ValueError("Database URL cannot be empty")

    url = make_url(database_url)
    if url.get_backend_name() != "postgresql":
        raise ValueError("DATABASE_URL must point to PostgreSQL")

    return url.set(drivername="postgresql+psycopg")


def create_sqlalchemy_engine(database_url: str) -> Engine:
    return create_engine(
        build_sqlalchemy_url(database_url),
        pool_pre_ping=True,
    )


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(
        bind=engine,
        expire_on_commit=False,
        autoflush=False,
    )
