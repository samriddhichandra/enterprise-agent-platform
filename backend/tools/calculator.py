"""
Calculator tool: safely evaluates arithmetic expressions.

Deliberately does NOT use eval() on raw text — instead it parses the
expression into an AST and only allows a fixed set of numeric operators.
This means "2 + 2" works but something like "__import__('os').system(...)"
is rejected before it ever executes, which matters once an LLM is the one
deciding what string to pass in.
"""
import ast
import operator

_ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.Mod: operator.mod,
}


def _eval_node(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPERATORS:
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        return _ALLOWED_OPERATORS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPERATORS:
        return _ALLOWED_OPERATORS[type(node.op)](_eval_node(node.operand))
    raise ValueError(f"Unsupported expression element: {ast.dump(node)}")


def calculate(expression: str) -> str:
    """
    Evaluates a basic arithmetic expression (+, -, *, /, %, **) and
    returns the result as a string, or an error message if the
    expression is invalid or unsafe.
    """
    try:
        tree = ast.parse(expression, mode="eval")
        result = _eval_node(tree.body)
        return str(result)
    except (SyntaxError, ValueError, ZeroDivisionError, TypeError) as e:
        return f"Error evaluating expression: {e}"
