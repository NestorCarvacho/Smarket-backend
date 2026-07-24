"""Migraciones livianas para columnas nuevas en deploys con create_all (SQLite/MySQL)."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection


async def ensure_schema(conn: AsyncConnection) -> None:
    dialect = conn.engine.dialect.name
    if dialect == "sqlite":
        result = await conn.execute(text("PRAGMA table_info(users)"))
        existing = {row[1] for row in result.fetchall()}
        alterations = [
            ("failed_login_attempts", "ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER NOT NULL DEFAULT 0"),
            ("is_locked", "ALTER TABLE users ADD COLUMN is_locked BOOLEAN NOT NULL DEFAULT 0"),
            ("reset_code_hash", "ALTER TABLE users ADD COLUMN reset_code_hash VARCHAR(255)"),
            ("reset_code_expires_at", "ALTER TABLE users ADD COLUMN reset_code_expires_at DATETIME"),
        ]
        for column, sql in alterations:
            if column not in existing:
                await conn.execute(text(sql))
        return

    if dialect in {"mysql", "mariadb"}:
        result = await conn.execute(
            text(
                """
                SELECT COLUMN_NAME FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'users'
                """
            )
        )
        existing = {row[0] for row in result.fetchall()}
        alterations = [
            (
                "failed_login_attempts",
                "ALTER TABLE users ADD COLUMN failed_login_attempts INT NOT NULL DEFAULT 0",
            ),
            ("is_locked", "ALTER TABLE users ADD COLUMN is_locked TINYINT(1) NOT NULL DEFAULT 0"),
            ("reset_code_hash", "ALTER TABLE users ADD COLUMN reset_code_hash VARCHAR(255) NULL"),
            (
                "reset_code_expires_at",
                "ALTER TABLE users ADD COLUMN reset_code_expires_at DATETIME NULL",
            ),
        ]
        for column, sql in alterations:
            if column not in existing:
                await conn.execute(text(sql))
