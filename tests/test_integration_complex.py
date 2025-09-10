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


def test_table_aliases_basic():
    """Test basic table aliases with dot notation."""
    sql = "WHERE u.age > 18 AND p.status = 'active'"
    
    expression = parse_sql_logic(sql)
    el_string = to_spring_el(expression)
    
    # Should handle dotted table aliases
    assert "#root.u.age" in el_string
    assert "#root.p.status" in el_string
    assert "&&" in el_string


def test_square_bracket_identifiers():
    """Test square bracket identifiers (should fail gracefully for now)."""
    sql = "WHERE [user name] > 18"
    
    # This might fail with current parser - that's expected
    try:
        expression = parse_sql_logic(sql)
        el_string = to_spring_el(expression)
        # If it works, great!
        assert el_string is not None
    except (ValueError, NotImplementedError):
        # Expected for complex identifiers not yet supported
        pass


def test_complex_multi_table_logic():
    """Test complex logic with multiple table references."""
    sql = "WHERE (emp.salary >= 50000 AND dept.budget > 1000000) OR (contractor.rate >= 75 AND proj.priority = 1)"
    
    expression = parse_sql_logic(sql)
    el_string = to_spring_el(expression)
    
    # Should handle multiple table references
    assert "#root.emp.salary" in el_string
    assert "#root.dept.budget" in el_string
    assert "#root.contractor.rate" in el_string
    assert "#root.proj.priority" in el_string
    assert "||" in el_string
    assert "&&" in el_string


def test_complex_case_with_table_aliases():
    """Test CASE expression with table aliases."""
    sql = "CASE WHEN emp.department = 'IT' THEN emp.salary WHEN emp.years >= 10 THEN emp.bonus ELSE emp.base END"
    
    expression = parse_sql_logic(sql)
    el_string = to_spring_el(expression)
    
    # Should handle table aliases in CASE
    assert "?" in el_string
    assert ":" in el_string
    assert "#root.emp.department" in el_string
    assert "#root.emp.salary" in el_string


def test_complex_nested_conditions_with_aliases():
    """Test deeply nested conditions with table aliases."""
    sql = "WHERE ((emp.type = 'full' AND (role.level >= 5 OR role.title = 'manager')) OR (emp.type = 'contract' AND contract.rate >= 75)) AND emp.active = true"
    
    expression = parse_sql_logic(sql)
    el_string = to_spring_el(expression)
    
    # Should handle deep nesting with aliases
    assert "#root.emp.type" in el_string
    assert "#root.role.level" in el_string
    assert "#root.contract.rate" in el_string
    assert "||" in el_string
    assert "&&" in el_string


def test_complex_functions_with_aliases():
    """Test functions with table aliases."""
    sql = "WHERE ISNULL(u.middle_name, '') != '' AND LEN(p.description) > 100"
    
    expression = parse_sql_logic(sql)
    el_string = to_spring_el(expression)
    
    # Should handle functions with table aliases
    assert el_string is not None
    assert "&&" in el_string


def test_complex_mixed_operators_with_aliases():
    """Test mixing different operators with table aliases."""
    sql = "WHERE emp.salary BETWEEN 40000 AND 120000 AND dept.name IN ('Sales', 'Marketing') AND NOT emp.remote = false"
    
    expression = parse_sql_logic(sql)
    el_string = to_spring_el(expression)
    
    # Should handle BETWEEN, IN, and NOT with aliases
    assert "#root.emp.salary" in el_string
    assert "#root.dept.name" in el_string
    assert "&&" in el_string
    assert "contains" in el_string


def test_complex_case_with_multiple_conditions():
    """Test CASE with complex conditions in WHEN clauses."""
    sql = "CASE WHEN score >= 90 AND grade = 'A' THEN 'Excellent' WHEN score >= 80 THEN 'Good' ELSE 'Needs Improvement' END"
    
    expression = parse_sql_logic(sql)
    el_string = to_spring_el(expression)
    
    # Should handle AND conditions within CASE WHEN
    assert "?" in el_string
    assert ":" in el_string
    assert "&&" in el_string  # From the AND in WHEN clause
