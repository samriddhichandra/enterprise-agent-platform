"""
SQL Query tool: lets an agent answer questions against the demo
`employees` and `orders` tables (e.g. "how many employees are in
Engineering?").

Uses a separate, synchronous SQLAlchemy engine from the one in
database/session.py. That async engine is used for persisting
conversation history from the FastAPI request handlers; this one is used
by the LangGraph Tool Agent node, which — like the rest of the graph —
runs synchronously. Keeping them separate avoids mixing sync/async
database calls inside a single graph node.

Safety approach — this only allows read queries, and only against a
known table whitelist:

  1. Reject anything that isn't a single SELECT statement.
  2. Reject any statement containing write/DDL keywords.
  3. Reject any table name not in ALLOWED_TABLES.

This is a deliberately conservative allowlist rather than a denylist,
because denylists are easy to bypass; for a demo/portfolio project this
is the right level of caution to be able to explain in an interview.
"""
import re

from sqlalchemy import create_engine, text

from backend.config import settings

ALLOWED_TABLES = {"employees", "orders"}
BLOCKED_KEYWORDS = {
    "insert", "update", "delete", "drop", "alter", "create",
    "truncate", "grant", "revoke", "attach", "exec", "execute", ";",
}

# database_url is configured for the async driver (postgresql+asyncpg://...);
# the sync tool engine needs the plain psycopg2 driver instead. Created
# lazily (not at import time) so that validate_query() can be used/tested
# without a database driver or live connection available.
_engine = None


def _get_engine():
    global _engine
    if _engine is None:
        sync_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
        _engine = create_engine(sync_url, pool_pre_ping=True)
    return _engine


class UnsafeQueryError(Exception):
    pass


def validate_query(query: str) -> None:
    q = query.strip().lower()

    if not q.startswith("select"):
        raise UnsafeQueryError("Only SELECT queries are allowed.")

    for keyword in BLOCKED_KEYWORDS:
        if keyword in q:
            raise UnsafeQueryError(f"Query contains a disallowed keyword: '{keyword}'")

    referenced_tables = re.findall(r"(?:from|join)\s+([a-zA-Z_][a-zA-Z0-9_]*)", q)
    if not referenced_tables:
        raise UnsafeQueryError("Could not identify a table in the query.")
    for table in referenced_tables:
        if table not in ALLOWED_TABLES:
            raise UnsafeQueryError(
                f"Query references table '{table}', which is not in the allowed list: {ALLOWED_TABLES}"
            )


def run_sql_query(query: str) -> str:
    """
    Validates and executes a read-only SQL query, returning the result
    as a simple formatted string (max 20 rows, to keep it readable in an
    LLM prompt).
    """
    try:
        validate_query(query)
    except UnsafeQueryError as e:
        return f"Query rejected: {e}"

    try:
        with _get_engine().connect() as conn:
            result = conn.execute(text(query))
            rows = result.fetchall()
            columns = result.keys()
    except Exception as e:
        return f"Query failed: {e}"

    if not rows:
        return "Query returned no rows."

    header = " | ".join(columns)
    body = "\n".join(" | ".join(str(v) for v in row) for row in rows[:20])
    return f"{header}\n{body}"
