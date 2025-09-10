import pytest
from mylibrary.parser import parse_sql_logic
from mylibrary.converter import to_spring_el


def test_complex_nested_conditions():
    """Test complex nested conditions."""
    sql = "WHERE (age > 18 AND (status = 'active' OR status = 'pending')) OR is_admin = true"
    
    expression = parse_sql_logic(sql)
    el_string = to_spring_el(expression)
    
    # Should handle nested logic
    assert el_string is not None
    assert "||" in el_string
    assert "&&" in el_string


def test_complex_with_functions():
    """Test complex expressions with functions."""
    sql = "WHERE ISNULL(name, 'Unknown') LIKE 'John%' AND age BETWEEN 18 AND 65"
    
    expression = parse_sql_logic(sql)
    el_string = to_spring_el(expression)
    
    # Should handle functions and BETWEEN
    assert el_string is not None


def test_complex_case_with_conditions():
    """Test CASE with complex conditions."""
    sql = "CASE WHEN age > 65 AND status = 'retired' THEN 'Senior' WHEN age > 18 THEN 'Adult' ELSE 'Minor' END"
    
    expression = parse_sql_logic(sql)
    el_string = to_spring_el(expression)
    
    # CASE expressions are now properly converted to ternary operators
    assert "?" in el_string  # Should contain ternary operator
    assert ":" in el_string  # Should contain ternary operator
    assert "#root.age > 65" in el_string
    assert "#root.age > 18" in el_string
    assert "'Senior'" in el_string
    assert "'Adult'" in el_string
    assert "'Minor'" in el_string


def test_complex_mixed_operators():
    """Test mixing different operators."""
    sql = "WHERE age >= 18 AND name NOT LIKE 'Test%' AND status IN ('active', 'pending')"
    
    expression = parse_sql_logic(sql)
    el_string = to_spring_el(expression)
    
    assert ">=" in el_string
    assert "NOT" not in el_string  # Should be converted
    assert "contains" in el_string


def test_complex_with_subqueries_placeholder():
    """Test complex expressions (subqueries not yet supported)."""
    # For now, test what we can
    sql = "WHERE age > 18"
    
    expression = parse_sql_logic(sql)
    el_string = to_spring_el(expression)
    
    assert el_string == "#root.age > 18"


def test_complex_error_recovery():
    """Test error handling in complex expressions."""
    sql = "WHERE age > AND status = 'active'"  # Malformed
    
    with pytest.raises(ValueError):
        expression = parse_sql_logic(sql)


def test_complex_large_expression():
    """Test performance with larger expressions."""
    sql = "WHERE age > 18 AND status = 'active' AND name LIKE 'John%' AND department IN ('IT', 'HR', 'Finance')"
    
    expression = parse_sql_logic(sql)
    el_string = to_spring_el(expression)
    
    # Should handle multiple conditions
    assert el_string.count("&&") >= 3


def test_complex_context_nesting():
    """Test with nested context."""
    sql = "WHERE user.age > 18 AND user.status = 'active'"
    
    expression = parse_sql_logic(sql)
    el_string = to_spring_el(expression, context="#root")
    
    # Should handle dotted variables
    assert "#root.user.age" in el_string


def test_case_with_additional_conditions():
    """Test CASE expression followed by additional logical operators."""
    sql = "CASE WHEN age > 65 AND status = 'retired' THEN 'Senior' WHEN age > 18 THEN 'Adult' ELSE 'Minor' END AND status IN ('active', 'pending')"
    
    expression = parse_sql_logic(sql)
    el_string = to_spring_el(expression)
    
    # Should parse as a compound expression with AND
    assert "&&" in el_string
    assert "?" in el_string  # Ternary operator from CASE
    assert ":" in el_string  # Ternary operator from CASE
    assert "contains" in el_string
    assert "active" in el_string
    assert "pending" in el_string
