import pytest
from mssql_to_spring_el.parser import parse_sql_logic
from mssql_to_spring_el.converter import to_spring_el


def test_integration_simple_where():
    """Test full integration: parse and convert simple WHERE clause."""
    sql = "WHERE age > 18"
    
    # Parse
    expression = parse_sql_logic(sql)
    
    # Convert
    el_string = to_spring_el(expression)
    
    assert el_string == "#root.age > 18"


def test_integration_compound_condition():
    """Test integration with compound conditions."""
    sql = "WHERE age > 18 AND status = 'active'"
    
    expression = parse_sql_logic(sql)
    el_string = to_spring_el(expression)
    
    assert el_string == "(#root.age > 18) && (#root.status == 'active')"


def test_integration_with_parentheses():
    """Test integration with parentheses."""
    sql = "WHERE (age > 18 OR age < 65) AND status = 'active'"
    
    expression = parse_sql_logic(sql)
    el_string = to_spring_el(expression)
    
    # Should handle parentheses correctly
    assert "||" in el_string
    assert "&&" in el_string


def test_integration_like_pattern():
    """Test integration with LIKE patterns."""
    sql = "WHERE name LIKE 'John%'"
    
    expression = parse_sql_logic(sql)
    el_string = to_spring_el(expression)
    
    assert "#root.name" in el_string
    assert "=~" in el_string or "matches" in el_string


def test_integration_in_list():
    """Test integration with IN lists."""
    sql = "WHERE status IN ('active', 'pending')"
    
    expression = parse_sql_logic(sql)
    el_string = to_spring_el(expression)
    
    assert "#root.status" in el_string
    assert "contains" in el_string


def test_integration_case_expression():
    """Test integration with CASE expressions."""
    sql = "CASE WHEN score >= 90 THEN 'A' WHEN score >= 80 THEN 'B' ELSE 'C' END"
    
    expression = parse_sql_logic(sql)
    el_string = to_spring_el(expression)
    
    # CASE expressions are now properly converted to ternary operators
    assert "?" in el_string
    assert ":" in el_string
    assert "#root.score >= 90" in el_string
    assert "'A'" in el_string


def test_integration_custom_context():
    """Test integration with custom context."""
    sql = "WHERE age > 18"
    
    expression = parse_sql_logic(sql)
    el_string = to_spring_el(expression, context="#user")
    
    assert el_string == "#user.age > 18"


def test_integration_error_handling():
    """Test integration error handling."""
    sql = "INVALID SQL"
    
    with pytest.raises(ValueError):
        expression = parse_sql_logic(sql)
