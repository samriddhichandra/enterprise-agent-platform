"""
Tests for the SQL tool's validation logic (the allowlist guardrails).
These test validate_query() directly rather than running real queries,
so they don't require a live PostgreSQL connection.
"""
import pytest

from backend.tools.sql_tool import validate_query, UnsafeQueryError


def test_allows_select_on_allowed_table():
    validate_query("SELECT COUNT(*) FROM employees")  # should not raise
    validate_query("SELECT * FROM orders WHERE status = 'completed'")  # should not raise


def test_allows_join_between_allowed_tables():
    validate_query(
        "SELECT e.name FROM employees e JOIN orders o ON e.id = o.id"
    )  # should not raise


def test_rejects_non_select_statements():
    with pytest.raises(UnsafeQueryError):
        validate_query("DELETE FROM employees")

    with pytest.raises(UnsafeQueryError):
        validate_query("UPDATE employees SET name = 'x'")

    with pytest.raises(UnsafeQueryError):
        validate_query("DROP TABLE employees")


def test_rejects_disallowed_table():
    with pytest.raises(UnsafeQueryError):
        validate_query("SELECT * FROM users")


def test_rejects_multiple_statements():
    with pytest.raises(UnsafeQueryError):
        validate_query("SELECT * FROM employees; DROP TABLE employees;")
