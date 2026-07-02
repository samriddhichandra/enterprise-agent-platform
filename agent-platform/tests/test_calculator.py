"""
Tests for the calculator tool, including the safety guardrails that
reject anything that isn't plain arithmetic.
"""
from backend.tools.calculator import calculate


def test_calculator_basic_arithmetic():
    assert calculate("2 + 2") == "4"
    assert calculate("10 - 3") == "7"
    assert calculate("6 * 7") == "42"
    assert calculate("10 / 4") == "2.5"


def test_calculator_operator_precedence():
    assert calculate("2 + 3 * 4") == "14"
    assert calculate("(2 + 3) * 4") == "20"


def test_calculator_rejects_unsafe_input():
    result = calculate("__import__('os').system('echo hi')")
    assert result.startswith("Error evaluating expression")


def test_calculator_rejects_division_by_zero():
    result = calculate("1 / 0")
    assert result.startswith("Error evaluating expression")


def test_calculator_rejects_non_numeric_names():
    result = calculate("x + 1")
    assert result.startswith("Error evaluating expression")
