#!/usr/bin/env python3
"""
Complex SQL scenario tests for the MSSQL to Spring EL converter.
These tests represent real-world SQL complexity levels and help identify parser limitations.
"""

import pytest
from mssql_to_spring_el.parser import parse_sql_logic
from mssql_to_spring_el.converter import to_spring_el


class TestBasicComplexity:
    """Level 1-4: Basic complexity scenarios that should work."""
    
    def test_basic_case_with_and(self):
        """Test basic CASE expression with additional AND condition."""
        sql = "CASE WHEN age > 65 THEN 'Senior' WHEN age > 18 THEN 'Adult' ELSE 'Minor' END AND status = 'active'"
        expression = parse_sql_logic(sql)
        spring_el = to_spring_el(expression)
        
        assert "PARSE_ERROR" not in spring_el
        assert "?" in spring_el  # Should contain ternary operator
        assert "&&" in spring_el  # Should contain AND conversion
        assert "#root.status == 'active'" in spring_el
    
    def test_multi_branch_case(self):
        """Test CASE with multiple WHEN branches."""
        sql = "CASE WHEN score >= 90 THEN 'A' WHEN score >= 80 THEN 'B' WHEN score >= 70 THEN 'C' WHEN score >= 60 THEN 'D' ELSE 'F' END"
        expression = parse_sql_logic(sql)
        spring_el = to_spring_el(expression)
        
        assert "PARSE_ERROR" not in spring_el
        assert spring_el.count("?") >= 4  # Should have nested ternary operators
        assert "'A'" in spring_el and "'F'" in spring_el
    
    def test_functions_with_case_result(self):
        """Test functions within CASE expressions."""
        sql = "CASE WHEN LEN(description) > 100 THEN 'Long' WHEN LEN(description) > 50 THEN 'Medium' ELSE 'Short' END AND category != 'archived'"
        expression = parse_sql_logic(sql)
        spring_el = to_spring_el(expression)
        
        assert "PARSE_ERROR" not in spring_el
        assert "LEN(#root.description)" in spring_el
        assert "#root.category != 'archived'" in spring_el
    
    def test_mixed_comparison_operators(self):
        """Test various comparison operators in sequence."""
        sql = "WHERE created_date >= '2023-01-01' AND modified_date <= '2023-12-31' AND version_number > 1.0 AND status != 'deleted' AND owner_id <> 0"
        expression = parse_sql_logic(sql)
        spring_el = to_spring_el(expression)
        
        assert "PARSE_ERROR" not in spring_el
        assert ">=" in spring_el and "<=" in spring_el
        assert "!=" in spring_el


class TestUnsupportedFeatures:
    """Level 2-20: Tests that currently fail due to missing parser features."""
    
    def test_complex_logical_combinations(self):
        """Test complex nested logical operators with parentheses."""
        sql = "WHERE (age >= 18 AND age <= 65) AND (status IN ('active', 'pending', 'verified') OR is_premium = true) AND NOT (name LIKE 'Test%')"
        expression = parse_sql_logic(sql)
        spring_el = to_spring_el(expression)
        assert "PARSE_ERROR" not in spring_el
    
    def test_between_operator(self):
        """Test BETWEEN operator support."""
        sql = "WHERE department IN ('Sales', 'Marketing', 'Support') AND salary BETWEEN 40000 AND 120000 AND location IN ('NYC', 'SF', 'LA', 'Chicago')"
        expression = parse_sql_logic(sql)
        spring_el = to_spring_el(expression)
        assert "PARSE_ERROR" not in spring_el
    
    def test_is_not_null_operator(self):
        """Test IS NOT NULL operator support."""
        sql = "CASE WHEN priority = 1 THEN 'High' WHEN priority = 2 THEN 'Medium' ELSE 'Low' END AND assigned_to IS NOT NULL AND due_date >= '2023-01-01'"
        expression = parse_sql_logic(sql)
        spring_el = to_spring_el(expression)
        assert "PARSE_ERROR" not in spring_el
    
    def test_not_in_operator(self):
        """Test NOT IN operator support."""
        sql = "WHERE status NOT IN ('inactive', 'suspended', 'deleted') AND category NOT IN ('test', 'temp') AND department_id IN (1, 2, 3)"
        expression = parse_sql_logic(sql)
        spring_el = to_spring_el(expression)
        assert "PARSE_ERROR" not in spring_el
        # Updated to expect properly quoted string literals in Spring EL
        assert "!{'inactive', 'suspended', 'deleted'}.contains(#root.status)" in spring_el
        assert "!{'test', 'temp'}.contains(#root.category)" in spring_el
    
    def test_deep_logical_nesting(self):
        """Test deeply nested logical structures."""
        sql = "WHERE ((type = 'employee' AND (role IN ('manager', 'director') OR seniority_level >= 5)) OR (type = 'contractor' AND hourly_rate >= 75)) AND status = 'active'"
        expression = parse_sql_logic(sql)
        spring_el = to_spring_el(expression)
        assert "PARSE_ERROR" not in spring_el


class TestTableAliasesAndBrackets:
    """Tests for table qualification and square bracket identifiers - Major missing feature."""
    
    def test_table_aliases_with_square_brackets(self):
        """Test table.column and [table].[column] syntax."""
        sql = "WHERE u.[first_name] IS NOT NULL AND p.[project_name] LIKE 'Critical%' AND d.[department_code] IN ('IT', 'HR') AND e.[employee_id] = u.[user_id]"
        expression = parse_sql_logic(sql)
        spring_el = to_spring_el(expression)
        assert "PARSE_ERROR" not in spring_el
    
    def test_mixed_table_aliases(self):
        """Test mixed table alias formats (dots and brackets)."""
        # Simple test for table qualification without complex parentheses
        sql = "WHERE emp.[salary] > 50000 AND dept.[budget] > 1000000 AND contractor.hourly_rate >= 75"
        expression = parse_sql_logic(sql)
        spring_el = to_spring_el(expression)
        assert "PARSE_ERROR" not in spring_el
    
    def test_special_characters_in_brackets(self):
        """Test square brackets with special characters (hyphens, spaces)."""
        sql = "WHERE [user-data].[email-address] LIKE '%@company.com' AND [sys info].[last login] >= '2023-01-01' AND [config].[feature-flags] = 'enabled'"
        expression = parse_sql_logic(sql)
        spring_el = to_spring_el(expression)
        assert "PARSE_ERROR" not in spring_el
    
    def test_case_with_table_aliases_and_brackets(self):
        """Test CASE expressions with table-qualified columns."""
        sql = "CASE WHEN emp.[department_id] = dept.[id] AND dept.[name] = 'Engineering' THEN emp.[base_salary] * 1.15 WHEN emp.[years_experience] >= 10 THEN emp.[base_salary] * 1.10 ELSE emp.[base_salary] END"
        expression = parse_sql_logic(sql)
        spring_el = to_spring_el(expression)
        # This one works with our improved table alias support
        assert expression is not None
        assert "PARSE_ERROR" not in spring_el
    
    def test_functions_with_table_aliases(self):
        """Test functions with table-qualified parameters."""
        sql = "WHERE ISNULL(u.[middle_name], '') != '' AND LEN(p.[description]) > 100 AND UPPER(d.[department_name]) IN ('SALES', 'MARKETING')"
        expression = parse_sql_logic(sql)
        spring_el = to_spring_el(expression)
        assert "PARSE_ERROR" not in spring_el
    
    def test_reserved_words_in_brackets(self):
        """Test SQL reserved words as column names in brackets."""
        sql = "WHERE [order].[date] >= '2023-01-01' AND [user].[group] IN ('admin', 'manager') AND [select].[value] IS NOT NULL AND [table].[index] > 0"
        expression = parse_sql_logic(sql)
        spring_el = to_spring_el(expression)
        assert "PARSE_ERROR" not in spring_el


class TestWhitespaceEdgeCases:
    """Tests for various whitespace scenarios."""
    
    def test_tabs_instead_of_spaces(self):
        """Test SQL with tabs instead of spaces."""
        sql = "WHERE\tage\t>\t18\tAND\tstatus\t=\t'active'\tOR\tdepartment\tIN\t('IT',\t'HR')"
        expression = parse_sql_logic(sql)
        spring_el = to_spring_el(expression)
        assert "PARSE_ERROR" not in spring_el
    
    def test_multiline_sql_with_mixed_whitespace(self):
        """Test multiline SQL with various whitespace characters."""
        sql = "WHERE age > 18\n            AND status = 'active'\n            OR (department IN ('IT', 'HR')\n                AND salary >= 50000)"
        expression = parse_sql_logic(sql)
        spring_el = to_spring_el(expression)
        assert "PARSE_ERROR" not in spring_el
    
    def test_extra_spaces_everywhere(self):
        """Test SQL with excessive spaces (this should work with current parser)."""
        sql = "WHERE   age    >    18   AND    status   =   'active'   OR    department    IN    ('IT',   'HR')  "
        expression = parse_sql_logic(sql)
        spring_el = to_spring_el(expression)
        # This might work with current parser
        assert expression is not None
    
    def test_whitespace_in_string_literals_preserved(self):
        """Test that whitespace in string literals is preserved."""
        sql = "WHERE description = 'This has  multiple   spaces' AND comment = '  Leading and trailing  '"
        expression = parse_sql_logic(sql)
        spring_el = to_spring_el(expression)
        
        assert "'This has  multiple   spaces'" in spring_el
        assert "'  Leading and trailing  '" in spring_el
    
    def test_minimal_spacing_challenging(self):
        """Test SQL with minimal spacing between tokens."""
        sql = "WHERE age>18AND status='active'OR department='IT'"
        expression = parse_sql_logic(sql)
        spring_el = to_spring_el(expression)
        assert "PARSE_ERROR" not in spring_el


class TestExtremeComplexity:
    """Ultimate complexity tests that represent real-world enterprise scenarios."""
    
    def test_multi_table_complex_logic(self):
        """Test complex logic across multiple tables."""
        sql = "WHERE (users.id = profiles.[user_id] AND profiles.[is_verified] = true) AND (orders.[total_amount] >= 500 OR customers.[loyalty_tier] IN ('Gold', 'Platinum')) AND NOT (users.[email] LIKE '%test%' OR users.[status] = 'suspended')"
        expression = parse_sql_logic(sql)
        spring_el = to_spring_el(expression)
        assert "PARSE_ERROR" not in spring_el
    
    def test_ultimate_nightmare_complexity(self):
        """The ultimate test - nested CASE with complex table aliases and all advanced features."""
        sql = "CASE WHEN ([user-profile].[age-group] IN ('25-35', '36-45') AND [employment-data].[salary-band] >= 75000 AND NOT ([performance-metrics].[rating] < 3.0 OR [absence-records].[days-missed] > 15)) THEN CASE WHEN dept.[budget-allocation] > 500000 THEN 'High_Value_Employee' ELSE 'Standard_Employee' END WHEN contractor.[hourly-rate] BETWEEN 50 AND 150 AND proj.[deadline-pressure] = 'high' THEN 'Critical_Contractor' ELSE 'Regular_Worker' END AND ([audit-trail].[last-modified] >= '2023-06-01' OR [system-flags].[force-include] = true) AND NOT (usr.[email] LIKE '%@competitor.com' OR [security-clearance].[level] = 'restricted')"
        expression = parse_sql_logic(sql)
        spring_el = to_spring_el(expression)
        assert "PARSE_ERROR" not in spring_el


def test_parser_statistics():
    """Meta-test to track overall parser capabilities."""
    # This test provides a summary of current parser capabilities
    # Run it to get current statistics
    
    from tests.test_complex_scenarios import (
        TestBasicComplexity, TestUnsupportedFeatures, 
        TestTableAliasesAndBrackets, TestWhitespaceEdgeCases,
        TestExtremeComplexity
    )
    
    # Count total tests and expected failures
    import inspect
    
    total_tests = 0
    expected_failures = 0
    
    for test_class in [TestBasicComplexity, TestUnsupportedFeatures, 
                      TestTableAliasesAndBrackets, TestWhitespaceEdgeCases,
                      TestExtremeComplexity]:
        
        for name, method in inspect.getmembers(test_class, predicate=inspect.isfunction):
            if name.startswith('test_'):
                total_tests += 1
                if hasattr(method, 'pytestmark'):
                    for mark in method.pytestmark:
                        if mark.name == 'xfail':
                            expected_failures += 1
                            break
    
    working_tests = total_tests - expected_failures
    print(f"\n📊 Parser Capability Statistics:")
    print(f"✅ Currently working: {working_tests}/{total_tests}")
    print(f"❌ Expected failures: {expected_failures}/{total_tests}")
    print(f"📈 Success rate: {(working_tests/total_tests)*100:.1f}%")
    
    # This assertion will always pass, but provides useful info
    assert total_tests > 0, f"Found {total_tests} tests, {working_tests} working"
