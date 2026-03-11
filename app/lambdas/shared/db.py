from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session

from shared import config

_engine = None


def get_engine():
    global _engine
    if _engine is None:
        url = URL.create(
            drivername="postgresql+psycopg2",
            username=config.DB_USERNAME,
            password=config.DB_PASSWORD,
            host=config.DB_HOST,
            port=int(config.DB_PORT),
            database=config.DB_NAME,
        )
        _engine = create_engine(url, pool_size=1, max_overflow=0)
    return _engine


@contextmanager
def get_session() -> Generator[Session, None, None]:
    engine = get_engine()
    with Session(engine, expire_on_commit=False) as session:
        yield session
