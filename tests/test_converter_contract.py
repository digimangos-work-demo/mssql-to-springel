import pytest
from mssql_to_spring_el.converter import to_spring_el
from mssql_to_spring_el.logic_models import BinaryOp, Variable, Literal


def test_convert_simple_comparison():
    """Test converting simple comparison to Spring EL."""
    expr = BinaryOp(Variable("age"), ">", Literal(18, "number"))
    result = to_spring_el(expr)
    
    assert result == "#root.age > 18"


def test_convert_compound_condition():
    """Test converting compound conditions with AND."""
    left = BinaryOp(Variable("status"), "=", Literal("active", "string"))
    right = BinaryOp(Variable("age"), ">", Literal(18, "number"))
    expr = BinaryOp(left, "AND", right)
    
    result = to_spring_el(expr)
    
    assert result == "(#root.status == 'active') && (#root.age > 18)"


def test_convert_with_custom_context():
    """Test converting with custom context."""
    expr = BinaryOp(Variable("age"), ">", Literal(18, "number"))
    result = to_spring_el(expr, context="#user")
    
    assert result == "#user.age > 18"


def test_convert_or_operator():
    """Test converting OR operator."""
    left = BinaryOp(Variable("status"), "=", Literal("active", "string"))
    right = BinaryOp(Variable("status"), "=", Literal("pending", "string"))
    expr = BinaryOp(left, "OR", right)
    
    result = to_spring_el(expr)
    
    assert result == "(#root.status == 'active') || (#root.status == 'pending')"


def test_convert_not_operator():
    """Test converting NOT operator."""
    # This will require UnaryOp
    # For now, test with BinaryOp
    expr = BinaryOp(Variable("active"), "=", Literal(True, "boolean"))
    result = to_spring_el(expr)
    
    assert result == "#root.active == true"


def test_convert_like_pattern():
    """Test converting LIKE to regex."""
    expr = BinaryOp(Variable("name"), "LIKE", Literal("John%", "string"))
    result = to_spring_el(expr)
    
    # LIKE should be converted to regex
    assert "#root.name =~" in result


def test_convert_in_list():
    """Test converting IN to contains."""
    # This might be more complex
    expr = BinaryOp(Variable("status"), "IN", Literal(["active", "pending"], "list"))
    result = to_spring_el(expr)
    
    assert ".contains(#root.status)" in result


def test_convert_is_null():
    """Test converting IS NULL."""
    # This will require UnaryOp for IS NULL
    expr = BinaryOp(Variable("name"), "IS", Literal(None, "null"))
    result = to_spring_el(expr)
    
    assert result == "#root.name == null"


def test_invalid_expression():
    """Test that invalid expressions raise ValueError."""
    # Pass invalid object
    with pytest.raises(ValueError):
        to_spring_el("invalid")


def test_empty_expression():
    """Test empty expression handling."""
    # This might not be needed
    pass
