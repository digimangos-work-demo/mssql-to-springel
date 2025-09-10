import pytest
from mylibrary.parser import parse_sql_logic
from mylibrary.logic_models import BinaryOp, Variable, Literal


def test_parse_simple_comparison():
    """Test parsing a simple WHERE clause with comparison."""
    sql = "WHERE age > 18"
    result = parse_sql_logic(sql)
    
    expected = BinaryOp(
        Variable("age"),
        ">",
        Literal(18, "number")
    )
    
    assert result == expected


def test_parse_compound_condition():
    """Test parsing compound conditions with AND."""
    sql = "WHERE status = 'active' AND age > 18"
    result = parse_sql_logic(sql)
    
    # This should be a BinaryOp with AND
    assert isinstance(result, BinaryOp)
    assert result.operator == "AND"
    
    # Left side: status = 'active'
    assert isinstance(result.left, BinaryOp)
    assert result.left.operator == "="
    assert isinstance(result.left.left, Variable)
    assert result.left.left.name == "status"
    assert isinstance(result.left.right, Literal)
    assert result.left.right.value == "active"
    assert result.left.right.value_type == "string"
    
    # Right side: age > 18
    assert isinstance(result.right, BinaryOp)
    assert result.right.operator == ">"
    assert isinstance(result.right.left, Variable)
    assert result.right.left.name == "age"
    assert isinstance(result.right.right, Literal)
    assert result.right.right.value == 18
    assert result.right.right.value_type == "number"


def test_parse_with_parentheses():
    """Test parsing expressions with parentheses."""
    sql = "WHERE (age > 18 AND status = 'active')"
    result = parse_sql_logic(sql)
    
    # Should handle parentheses
    assert isinstance(result, BinaryOp)
    assert result.operator == "AND"


def test_parse_unary_operator():
    """Test parsing unary operators like NOT."""
    sql = "WHERE NOT (age < 18)"
    result = parse_sql_logic(sql)
    
    # Should parse NOT
    # This will be implemented later
    assert result is not None


def test_parse_like_pattern():
    """Test parsing LIKE patterns."""
    sql = "WHERE name LIKE 'John%'"
    result = parse_sql_logic(sql)
    
    assert isinstance(result, BinaryOp)
    assert result.operator == "LIKE"


def test_parse_in_list():
    """Test parsing IN lists."""
    sql = "WHERE status IN ('active', 'pending')"
    result = parse_sql_logic(sql)
    
    assert isinstance(result, BinaryOp)
    assert result.operator == "IN"


def test_parse_case_expression():
    """Test parsing CASE expressions."""
    sql = "CASE WHEN score >= 90 THEN 'A' ELSE 'B' END"
    result = parse_sql_logic(sql)
    
    # CASE parsing will be implemented
    assert result is not None


def test_invalid_sql_syntax():
    """Test that invalid SQL raises ValueError."""
    sql = "INVALID SQL HERE"
    with pytest.raises(ValueError):
        parse_sql_logic(sql)


def test_unsupported_operator():
    """Test that unsupported operators raise NotImplementedError."""
    sql = "WHERE age MOD 2 = 0"  # MOD might not be supported
    with pytest.raises(NotImplementedError):
        parse_sql_logic(sql)


def test_malformed_expression():
    """Test malformed expressions raise ValueError."""
    sql = "WHERE age >"
    with pytest.raises(ValueError):
        parse_sql_logic(sql)
