"""
Object model classes for MSSQL logical expressions.

This module defines the abstract syntax tree (AST) classes that represent
parsed MSSQL logic expressions.
"""

from typing import Any, List, Dict


class Expression:
    """Base class for all logic expression nodes."""

    def __init__(self):
        pass

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for JSON output."""
        return {"type": self.__class__.__name__}

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}()"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Expression):
            return False
        return self.__dict__ == other.__dict__


class BinaryOp(Expression):
    """Represents binary operations like >, =, AND, etc."""

    def __init__(self, left: Expression, operator: str, right: Expression):
        super().__init__()
        self.left = left
        self.operator = operator
        self.right = right

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "BinaryOp",
            "left": self.left.to_dict(),
            "operator": self.operator,
            "right": self.right.to_dict()
        }

    def __repr__(self) -> str:
        return f"BinaryOp({self.left!r}, {self.operator!r}, {self.right!r})"


class UnaryOp(Expression):
    """Represents unary operations like NOT, IS NULL."""

    def __init__(self, operator: str, operand: Expression):
        super().__init__()
        self.operator = operator
        self.operand = operand

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "UnaryOp",
            "operator": self.operator,
            "operand": self.operand.to_dict()
        }

    def __repr__(self) -> str:
        return f"UnaryOp({self.operator!r}, {self.operand!r})"


class FunctionCall(Expression):
    """Represents function calls like ISNULL(column, 'default')."""

    def __init__(self, name: str, arguments: List[Expression]):
        super().__init__()
        self.name = name
        self.arguments = arguments

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "FunctionCall",
            "name": self.name,
            "arguments": [arg.to_dict() for arg in self.arguments]
        }

    def __repr__(self) -> str:
        return f"FunctionCall({self.name!r}, {self.arguments!r})"


class Literal(Expression):
    """Represents literal values like strings, numbers, booleans."""

    def __init__(self, value: Any, value_type: str):
        super().__init__()
        self.value = value
        self.value_type = value_type  # 'string', 'number', 'boolean'

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "Literal",
            "value": self.value,
            "value_type": self.value_type
        }

    def __repr__(self) -> str:
        return f"Literal({self.value!r}, {self.value_type!r})"


class Variable(Expression):
    """Represents column names or variables."""

    def __init__(self, name: str):
        super().__init__()
        self.name = name

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "Variable",
            "name": self.name
        }

    def __repr__(self) -> str:
        return f"Variable({self.name!r})"


class Conditional(Expression):
    """Represents CASE/IIF expressions."""

    def __init__(self, condition: Expression, then_expr: Expression, else_expr: Expression):
        super().__init__()
        self.condition = condition
        self.then_expr = then_expr
        self.else_expr = else_expr

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "Conditional",
            "condition": self.condition.to_dict(),
            "then": self.then_expr.to_dict(),
            "else": self.else_expr.to_dict()
        }

    def __repr__(self) -> str:
        return f"Conditional({self.condition!r}, {self.then_expr!r}, {self.else_expr!r})"


class LogicalGroup(Expression):
    """Represents grouped expressions with parentheses."""

    def __init__(self, expression: Expression):
        super().__init__()
        self.expression = expression

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "LogicalGroup",
            "expression": self.expression.to_dict()
        }

    def __repr__(self) -> str:
        return f"LogicalGroup({self.expression!r})"
