from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from shared import config

_engine = None


def get_engine():
    global _engine
    if _engine is None:
        url = (
            f"postgresql+psycopg2://{config.DB_USERNAME}:{config.DB_PASSWORD}"
            f"@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}"
        )
        _engine = create_engine(url, pool_size=1, max_overflow=0)
    return _engine


@contextmanager
def get_session() -> Generator[Session, None, None]:
    engine = get_engine()
    with Session(engine) as session:
        yield session
