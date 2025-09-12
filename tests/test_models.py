"""
Unit tests for logic model classes.

Tests all Expression subclasses for proper functionality, serialization,
and equality comparison.
"""

import pytest
from mssql_to_spring_el.logic_models import (
    Expression, BinaryOp, UnaryOp, FunctionCall,
    Literal, Variable, Conditional, LogicalGroup
)


class TestExpression:
    """Test the base Expression class."""

    def test_base_expression_creation(self):
        """Test creating a base Expression."""
        expr = Expression()
        assert isinstance(expr, Expression)

    def test_base_expression_to_dict(self):
        """Test serialization of base Expression."""
        expr = Expression()
        result = expr.to_dict()
        assert result == {"type": "Expression"}

    def test_base_expression_repr(self):
        """Test string representation of base Expression."""
        expr = Expression()
        assert repr(expr) == "Expression()"

    def test_base_expression_equality(self):
        """Test equality comparison of base Expression."""
        expr1 = Expression()
        expr2 = Expression()
        assert expr1 == expr2
        assert expr1 != "not an expression"


class TestBinaryOp:
    """Test the BinaryOp class."""

    def test_binary_op_creation(self):
        """Test creating a BinaryOp."""
        left = Variable("age")
        right = Literal(25, "number")
        op = BinaryOp(left, ">", right)
        
        assert op.left == left
        assert op.operator == ">"
        assert op.right == right

    def test_binary_op_to_dict(self):
        """Test serialization of BinaryOp."""
        left = Variable("age")
        right = Literal(25, "number")
        op = BinaryOp(left, ">", right)
        
        result = op.to_dict()
        expected = {
            "type": "BinaryOp",
            "left": {"type": "Variable", "name": "age"},
            "operator": ">",
            "right": {"type": "Literal", "value": 25, "value_type": "number"}
        }
        assert result == expected

    def test_binary_op_repr(self):
        """Test string representation of BinaryOp."""
        left = Variable("age")
        right = Literal(25, "number")
        op = BinaryOp(left, ">", right)
        
        expected = "BinaryOp(Variable('age'), '>', Literal(25, 'number'))"
        assert repr(op) == expected

    def test_binary_op_equality(self):
        """Test equality comparison of BinaryOp."""
        left = Variable("age")
        right = Literal(25, "number")
        op1 = BinaryOp(left, ">", right)
        op2 = BinaryOp(left, ">", right)
        op3 = BinaryOp(left, "<", right)
        
        assert op1 == op2
        assert op1 != op3


class TestUnaryOp:
    """Test the UnaryOp class."""

    def test_unary_op_creation(self):
        """Test creating a UnaryOp."""
        operand = Variable("active")
        op = UnaryOp("NOT", operand)
        
        assert op.operator == "NOT"
        assert op.operand == operand

    def test_unary_op_to_dict(self):
        """Test serialization of UnaryOp."""
        operand = Variable("active")
        op = UnaryOp("NOT", operand)
        
        result = op.to_dict()
        expected = {
            "type": "UnaryOp",
            "operator": "NOT",
            "operand": {"type": "Variable", "name": "active"}
        }
        assert result == expected

    def test_unary_op_repr(self):
        """Test string representation of UnaryOp."""
        operand = Variable("active")
        op = UnaryOp("NOT", operand)
        
        expected = "UnaryOp('NOT', Variable('active'))"
        assert repr(op) == expected

    def test_unary_op_equality(self):
        """Test equality comparison of UnaryOp."""
        operand = Variable("active")
        op1 = UnaryOp("NOT", operand)
        op2 = UnaryOp("NOT", operand)
        op3 = UnaryOp("!", operand)
        
        assert op1 == op2
        assert op1 != op3


class TestFunctionCall:
    """Test the FunctionCall class."""

    def test_function_call_creation(self):
        """Test creating a FunctionCall."""
        args = [Variable("name"), Literal("Unknown", "string")]
        func = FunctionCall("ISNULL", args)
        
        assert func.name == "ISNULL"
        assert func.arguments == args

    def test_function_call_no_args(self):
        """Test creating a FunctionCall with no arguments."""
        func = FunctionCall("GETDATE", [])
        
        assert func.name == "GETDATE"
        assert func.arguments == []

    def test_function_call_to_dict(self):
        """Test serialization of FunctionCall."""
        args = [Variable("name"), Literal("Unknown", "string")]
        func = FunctionCall("ISNULL", args)
        
        result = func.to_dict()
        expected = {
            "type": "FunctionCall",
            "name": "ISNULL",
            "arguments": [
                {"type": "Variable", "name": "name"},
                {"type": "Literal", "value": "Unknown", "value_type": "string"}
            ]
        }
        assert result == expected

    def test_function_call_repr(self):
        """Test string representation of FunctionCall."""
        args = [Variable("name"), Literal("Unknown", "string")]
        func = FunctionCall("ISNULL", args)
        
        expected = "FunctionCall('ISNULL', [Variable('name'), Literal('Unknown', 'string')])"
        assert repr(func) == expected

    def test_function_call_equality(self):
        """Test equality comparison of FunctionCall."""
        args = [Variable("name"), Literal("Unknown", "string")]
        func1 = FunctionCall("ISNULL", args)
        func2 = FunctionCall("ISNULL", args)
        func3 = FunctionCall("COALESCE", args)
        
        assert func1 == func2
        assert func1 != func3


class TestLiteral:
    """Test the Literal class."""

    def test_literal_string_creation(self):
        """Test creating a string Literal."""
        lit = Literal("John", "string")
        
        assert lit.value == "John"
        assert lit.value_type == "string"

    def test_literal_number_creation(self):
        """Test creating a number Literal."""
        lit = Literal(42, "number")
        
        assert lit.value == 42
        assert lit.value_type == "number"

    def test_literal_boolean_creation(self):
        """Test creating a boolean Literal."""
        lit = Literal(True, "boolean")
        
        assert lit.value is True
        assert lit.value_type == "boolean"

    def test_literal_null_creation(self):
        """Test creating a null Literal."""
        lit = Literal(None, "null")
        
        assert lit.value is None
        assert lit.value_type == "null"

    def test_literal_to_dict(self):
        """Test serialization of Literal."""
        lit = Literal("John", "string")
        
        result = lit.to_dict()
        expected = {
            "type": "Literal",
            "value": "John",
            "value_type": "string"
        }
        assert result == expected

    def test_literal_repr(self):
        """Test string representation of Literal."""
        lit = Literal("John", "string")
        
        expected = "Literal('John', 'string')"
        assert repr(lit) == expected

    def test_literal_equality(self):
        """Test equality comparison of Literal."""
        lit1 = Literal("John", "string")
        lit2 = Literal("John", "string")
        lit3 = Literal("Jane", "string")
        
        assert lit1 == lit2
        assert lit1 != lit3


class TestVariable:
    """Test the Variable class."""

    def test_variable_creation(self):
        """Test creating a Variable."""
        var = Variable("username")
        
        assert var.name == "username"

    def test_variable_to_dict(self):
        """Test serialization of Variable."""
        var = Variable("username")
        
        result = var.to_dict()
        expected = {
            "type": "Variable",
            "name": "username"
        }
        assert result == expected

    def test_variable_repr(self):
        """Test string representation of Variable."""
        var = Variable("username")
        
        expected = "Variable('username')"
        assert repr(var) == expected

    def test_variable_equality(self):
        """Test equality comparison of Variable."""
        var1 = Variable("username")
        var2 = Variable("username")
        var3 = Variable("email")
        
        assert var1 == var2
        assert var1 != var3


class TestConditional:
    """Test the Conditional class."""

    def test_conditional_creation(self):
        """Test creating a Conditional."""
        condition = BinaryOp(Variable("age"), ">", Literal(18, "number"))
        true_expr = Literal("Adult", "string")
        false_expr = Literal("Minor", "string")
        
        cond = Conditional(condition, true_expr, false_expr)
        
        assert cond.condition == condition
        assert cond.then_expr == true_expr
        assert cond.else_expr == false_expr

    def test_conditional_to_dict(self):
        """Test serialization of Conditional."""
        condition = BinaryOp(Variable("age"), ">", Literal(18, "number"))
        true_expr = Literal("Adult", "string")
        false_expr = Literal("Minor", "string")
        
        cond = Conditional(condition, true_expr, false_expr)
        
        result = cond.to_dict()
        expected = {
            "type": "Conditional",
            "condition": {
                "type": "BinaryOp",
                "left": {"type": "Variable", "name": "age"},
                "operator": ">",
                "right": {"type": "Literal", "value": 18, "value_type": "number"}
            },
            "then": {"type": "Literal", "value": "Adult", "value_type": "string"},
            "else": {"type": "Literal", "value": "Minor", "value_type": "string"}
        }
        assert result == expected

    def test_conditional_repr(self):
        """Test string representation of Conditional."""
        condition = BinaryOp(Variable("age"), ">", Literal(18, "number"))
        true_expr = Literal("Adult", "string")
        false_expr = Literal("Minor", "string")
        
        cond = Conditional(condition, true_expr, false_expr)
        
        expected = ("Conditional(BinaryOp(Variable('age'), '>', Literal(18, 'number')), "
                   "Literal('Adult', 'string'), Literal('Minor', 'string'))")
        assert repr(cond) == expected

    def test_conditional_equality(self):
        """Test equality comparison of Conditional."""
        condition = BinaryOp(Variable("age"), ">", Literal(18, "number"))
        true_expr = Literal("Adult", "string")
        false_expr = Literal("Minor", "string")
        
        cond1 = Conditional(condition, true_expr, false_expr)
        cond2 = Conditional(condition, true_expr, false_expr)
        cond3 = Conditional(condition, false_expr, true_expr)
        
        assert cond1 == cond2
        assert cond1 != cond3


class TestLogicalGroup:
    """Test the LogicalGroup class."""

    def test_logical_group_creation(self):
        """Test creating a LogicalGroup."""
        expr = BinaryOp(Variable("age"), ">", Literal(18, "number"))
        group = LogicalGroup(expr)
        
        assert group.expression == expr

    def test_logical_group_to_dict(self):
        """Test serialization of LogicalGroup."""
        expr = BinaryOp(Variable("age"), ">", Literal(18, "number"))
        group = LogicalGroup(expr)
        
        result = group.to_dict()
        expected = {
            "type": "LogicalGroup",
            "expression": {
                "type": "BinaryOp",
                "left": {"type": "Variable", "name": "age"},
                "operator": ">",
                "right": {"type": "Literal", "value": 18, "value_type": "number"}
            }
        }
        assert result == expected

    def test_logical_group_repr(self):
        """Test string representation of LogicalGroup."""
        expr = BinaryOp(Variable("age"), ">", Literal(18, "number"))
        group = LogicalGroup(expr)
        
        expected = "LogicalGroup(BinaryOp(Variable('age'), '>', Literal(18, 'number')))"
        assert repr(group) == expected

    def test_logical_group_equality(self):
        """Test equality comparison of LogicalGroup."""
        expr = BinaryOp(Variable("age"), ">", Literal(18, "number"))
        group1 = LogicalGroup(expr)
        group2 = LogicalGroup(expr)
        
        other_expr = BinaryOp(Variable("name"), "=", Literal("John", "string"))
        group3 = LogicalGroup(other_expr)
        
        assert group1 == group2
        assert group1 != group3
