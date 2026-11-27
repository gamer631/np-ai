"""Bounded, dependency-free mathematical expression evaluator for NIL research."""
from __future__ import annotations

import ast
import math
from typing import Callable

MAX_EXPRESSION_LENGTH = 256
MAX_AST_NODES = 64
MAX_AST_DEPTH = 16
MAX_EXPONENT = 100

_FUNCTIONS: dict[str, Callable[..., float]] = {
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "log10": math.log10,
    "exp": math.exp,
    "abs": abs,
    "floor": math.floor,
    "ceil": math.ceil,
}
_CONSTANTS = {"pi": math.pi, "e": math.e}


class CalculationError(ValueError):
    """Raised when an expression is invalid or outside evaluator limits."""


def _check_tree(node: ast.AST) -> None:
    nodes = list(ast.walk(node))
    if len(nodes) > MAX_AST_NODES:
        raise CalculationError("expression contains too many operations")

    def depth(current: ast.AST, level: int) -> None:
        if level > MAX_AST_DEPTH:
            raise CalculationError("expression is too deeply nested")
        for child in ast.iter_child_nodes(current):
            depth(child, level + 1)

    depth(node, 0)


def _evaluate(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _evaluate(node.body)
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        return float(node.value)
    if isinstance(node, ast.Name):
        if node.id in _CONSTANTS:
            return _CONSTANTS[node.id]
        raise CalculationError(f"unknown constant: {node.id}")
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        value = _evaluate(node.operand)
        return value if isinstance(node.op, ast.UAdd) else -value
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow)):
        left, right = _evaluate(node.left), _evaluate(node.right)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            if right == 0:
                raise CalculationError("division by zero")
            return left / right
        if abs(right) > MAX_EXPONENT:
            raise CalculationError("exponent exceeds evaluator limit")
        return left**right
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        if node.keywords:
            raise CalculationError("keyword arguments are not supported")
        function = _FUNCTIONS.get(node.func.id)
        if function is None:
            raise CalculationError(f"unsupported function: {node.func.id}")
        return float(function(*[_evaluate(arg) for arg in node.args]))
    raise CalculationError(f"unsupported expression element: {type(node).__name__}")


def calculate(expression: str) -> float:
    """Evaluate a bounded math expression; never executes Python code."""
    if not isinstance(expression, str):
        raise TypeError("expression must be a string")
    if not expression.strip() or len(expression) > MAX_EXPRESSION_LENGTH:
        raise CalculationError("expression is empty or exceeds length limit")
    try:
        tree = ast.parse(expression, mode="eval")
        _check_tree(tree)
        result = _evaluate(tree)
    except (SyntaxError, ValueError, TypeError, OverflowError, ZeroDivisionError) as exc:
        if isinstance(exc, CalculationError):
            raise
        raise CalculationError("invalid or out-of-range mathematical expression") from exc
    if not math.isfinite(result):
        raise CalculationError("result is not finite")
    return result
