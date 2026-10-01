import os
os.environ["LIFE_OS_DB_URL"] = "sqlite:///:memory:"
os.environ.pop("LIFE_OS_API_TOKEN", None)

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.db import Base
from app import models  # noqa: F401


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    with engine.begin() as conn:
        conn.execute(text("CREATE VIRTUAL TABLE course_chunks_fts USING fts5(chunk_id UNINDEXED,module,topic,title,content,tokenize='porter unicode61')"))
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    s = Session()
    try:
        yield s
    finally:
        s.close()
