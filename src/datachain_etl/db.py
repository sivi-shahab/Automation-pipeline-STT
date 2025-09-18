"""Database utilities for interacting with Postgres."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator, Iterable, List, Mapping

import psycopg
from psycopg.rows import dict_row

from .config import DatabaseConfig

Record = Mapping[str, object]


@contextmanager
def get_connection(config: DatabaseConfig) -> Generator[psycopg.Connection, None, None]:
    """Yield a Postgres connection configured via :class:`DatabaseConfig`."""

    conn = psycopg.connect(
        host=config.host,
        port=config.port,
        dbname=config.dbname,
        user=config.user,
        password=config.password,
        connect_timeout=config.connect_timeout,
        row_factory=dict_row,
    )
    try:
        yield conn
    finally:
        conn.close()


def fetch_pending_records(
    conn: psycopg.Connection, query: str, batch_size: int
) -> List[Record]:
    """Retrieve records that need to be processed by the ETL job."""

    with conn.cursor() as cur:
        cur.execute(query, {"batch_size": batch_size})
        rows = cur.fetchall()
    return rows


def mark_records_processed(
    conn: psycopg.Connection,
    ticket_ids: Iterable[str],
    *,
    table: str = "audio_jobs",
) -> None:
    """Mark the provided ticket IDs as processed."""

    if not ticket_ids:
        return
    with conn.cursor() as cur:
        cur.execute(
            f"""
            UPDATE {table}
            SET processed_at = NOW()
            WHERE ticket_id = ANY(%(ticket_ids)s)
            """,
            {"ticket_ids": list(ticket_ids)},
        )
    conn.commit()
