from sqlalchemy import create_engine, text

from app.db import _apply_sqlite_compat_migrations


def test_compat_migration_adds_adguard_ownership_column_to_existing_table():
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE focus_domain_rules (
                id INTEGER PRIMARY KEY,
                domain VARCHAR(255) NOT NULL,
                reason VARCHAR(255),
                enabled BOOLEAN NOT NULL DEFAULT 1,
                created_at DATETIME
            )
        """))
        _apply_sqlite_compat_migrations(conn)
        columns = {
            row["name"]
            for row in conn.execute(text('PRAGMA table_info("focus_domain_rules")')).mappings().all()
        }
        assert "adguard_rule_owned" in columns


def test_compat_migration_is_idempotent():
    engine = create_engine("sqlite:///:memory:")
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE focus_domain_rules (
                id INTEGER PRIMARY KEY,
                domain VARCHAR(255) NOT NULL,
                reason VARCHAR(255),
                enabled BOOLEAN NOT NULL DEFAULT 1,
                adguard_rule_owned BOOLEAN NOT NULL DEFAULT 0,
                created_at DATETIME
            )
        """))
        _apply_sqlite_compat_migrations(conn)
        _apply_sqlite_compat_migrations(conn)
        columns = [
            row["name"]
            for row in conn.execute(text('PRAGMA table_info("focus_domain_rules")')).mappings().all()
        ]
        assert columns.count("adguard_rule_owned") == 1
