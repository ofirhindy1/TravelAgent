"""
Postgres helpers: token-usage tracking and cancellation audit log.

Schema
------
thread_token_usage
  thread_id    TEXT PRIMARY KEY
  total_tokens INTEGER  (cumulative input + output tokens for this thread)
  updated_at   TIMESTAMPTZ

cancellation_log
  id           SERIAL PRIMARY KEY
  thread_id    TEXT         (one row per cancellation event)
  cancelled_at TIMESTAMPTZ
"""
import logging

from psycopg_pool import AsyncConnectionPool

logger = logging.getLogger(__name__)

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS thread_token_usage (
    thread_id    TEXT        PRIMARY KEY,
    total_tokens INTEGER     NOT NULL DEFAULT 0,
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""

_UPSERT_TOKENS = """
INSERT INTO thread_token_usage (thread_id, total_tokens, updated_at)
VALUES (%s, %s, NOW())
ON CONFLICT (thread_id) DO UPDATE
    SET total_tokens = thread_token_usage.total_tokens + EXCLUDED.total_tokens,
        updated_at   = NOW();
"""

_SELECT_TOKENS = """
SELECT total_tokens FROM thread_token_usage WHERE thread_id = %s;
"""

_CREATE_CANCELLATION_TABLE = """
CREATE TABLE IF NOT EXISTS cancellation_log (
    id           SERIAL       PRIMARY KEY,
    thread_id    TEXT         NOT NULL,
    cancelled_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
"""

_CREATE_CANCELLATION_INDEX = """
CREATE INDEX IF NOT EXISTS idx_cancellation_thread ON cancellation_log (thread_id);
"""

_INSERT_CANCELLATION = """
INSERT INTO cancellation_log (thread_id, cancelled_at)
VALUES (%s, NOW());
"""

# Delete order matters: writes/blobs before checkpoints (safe even without FK constraints)
_CLEAR_THREAD = [
    "DELETE FROM checkpoint_writes  WHERE thread_id = %s;",
    "DELETE FROM checkpoint_blobs   WHERE thread_id = %s;",
    "DELETE FROM checkpoints        WHERE thread_id = %s;",
    "DELETE FROM thread_token_usage WHERE thread_id = %s;",
]


async def setup_token_table(pool: AsyncConnectionPool) -> None:
    """Create the token-usage table if it does not already exist."""
    async with pool.connection() as conn:
        await conn.execute(_CREATE_TABLE)


async def setup_cancellation_table(pool: AsyncConnectionPool) -> None:
    """Create the cancellation audit-log table if it does not already exist."""
    async with pool.connection() as conn:
        await conn.execute(_CREATE_CANCELLATION_TABLE)
        await conn.execute(_CREATE_CANCELLATION_INDEX)


async def get_thread_tokens(pool: AsyncConnectionPool, thread_id: str) -> int:
    """Return the cumulative token count for *thread_id* (0 if unknown)."""
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(_SELECT_TOKENS, (thread_id,))
            row = await cur.fetchone()
            return int(row[0]) if row else 0


async def clear_thread_data(pool: AsyncConnectionPool, thread_id: str) -> None:
    """
    Delete all Postgres data for *thread_id*:
      - LangGraph checkpoint tables (writes → blobs → checkpoints)
      - Our own token-usage row

    Safe to call even if the thread never existed.
    """
    try:
        async with pool.connection() as conn:
            for sql in _CLEAR_THREAD:
                await conn.execute(sql, (thread_id,))
        logger.info("Cleared all data for thread %s", thread_id)
    except Exception:
        logger.exception("Failed to clear data for thread %s", thread_id)


async def log_cancellation(pool: AsyncConnectionPool, thread_id: str) -> None:
    """Insert one row into cancellation_log for auditability."""
    try:
        async with pool.connection() as conn:
            await conn.execute(_INSERT_CANCELLATION, (thread_id,))
        logger.info("Logged cancellation for thread %s", thread_id)
    except Exception:
        logger.exception("Failed to log cancellation for thread %s", thread_id)


async def add_thread_tokens(
    pool: AsyncConnectionPool,
    thread_id: str,
    tokens: int,
) -> None:
    """Increment the token counter for *thread_id* by *tokens*."""
    if tokens <= 0:
        return
    try:
        async with pool.connection() as conn:
            await conn.execute(_UPSERT_TOKENS, (thread_id, tokens))
    except Exception:
        logger.exception("Failed to persist token usage for thread %s", thread_id)
