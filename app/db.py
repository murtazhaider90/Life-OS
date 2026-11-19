from pathlib import Path
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from .config import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()
if settings.db_url.startswith("sqlite:///./"):
    Path(settings.db_url.removeprefix("sqlite:///./")).parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    settings.db_url,
    connect_args={"check_same_thread": False} if settings.db_url.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@event.listens_for(engine, "connect")
def _sqlite_pragmas(dbapi_connection, _):
    if settings.db_url.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.close()


def _sqlite_columns(conn, table_name: str) -> set[str]:
    rows = conn.execute(text(f'PRAGMA table_info("{table_name}")')).mappings().all()
    return {str(row["name"]) for row in rows}


def _apply_sqlite_compat_migrations(conn) -> None:
    # create_all() creates new tables but does not add columns to existing SQLite tables.
    # Keep these tiny additive migrations explicit and deterministic for local upgrades.
    tables = {
        str(row["name"])
        for row in conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table'")
        ).mappings().all()
    }

    if "focus_domain_rules" in tables:
        columns = _sqlite_columns(conn, "focus_domain_rules")
        if "adguard_rule_owned" not in columns:
            conn.execute(
                text(
                    "ALTER TABLE focus_domain_rules "
                    "ADD COLUMN adguard_rule_owned BOOLEAN NOT NULL DEFAULT 0"
                )
            )


def init_db() -> None:
    from . import context_models, models  # noqa: F401

    Base.metadata.create_all(engine)
    if settings.db_url.startswith("sqlite"):
        with engine.begin() as conn:
            _apply_sqlite_compat_migrations(conn)
            conn.execute(text("""
                CREATE VIRTUAL TABLE IF NOT EXISTS course_chunks_fts USING fts5(
                    chunk_id UNINDEXED,
                    module,
                    topic,
                    title,
                    content,
                    tokenize='porter unicode61'
                )
            """))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
