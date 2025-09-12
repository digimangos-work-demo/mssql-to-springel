"""
Tests for complex parsing edge cases and ultimate SQL complexity scenarios.
These tests target the specific issues found in enterprise-level SQL expressions.
"""

import pytest
from mssql_to_spring_el.parser import parse_sql_logic
from mssql_to_spring_el.converter import to_spring_el


class TestComplexParsingFixes:
    """Tests for fixing complex parsing edge cases."""

    def test_not_operator_precedence_with_parentheses(self):
        """Test that NOT properly respects parentheses grouping."""
        test_cases = [
            {
                'sql': 'WHERE NOT ([performance-metrics].[rating] < 3.0 OR [absence-records].[days-missed] > 15)',
                'description': 'NOT with complex parenthesized OR expression',
                'should_contain': ['!(', '||', ')'],
                'should_not_contain': ['!#root.', '#root.3.0']
            },
            {
                'sql': 'WHERE NOT (age < 18 AND status = "inactive")',
                'description': 'NOT with simple parenthesized AND expression',
                'should_contain': ['!(', '&&', ')'],
                'should_not_contain': ['!#root.']
            },
            {
                'sql': 'WHERE NOT (dept IN ("HR", "Finance") OR salary > 100000)',
                'description': 'NOT with IN clause and OR',
                'should_contain': ['!(', '.contains(', '||', ')'],
                'should_not_contain': ['!#root.', ' IN (']
            }
        ]
        
        for case in test_cases:
            expression = parse_sql_logic(case['sql'])
            spring_el = to_spring_el(expression)
            
            # Check required patterns
            for pattern in case['should_contain']:
                assert pattern in spring_el, \
                    f"{case['description']}: Missing pattern '{pattern}' in: {spring_el}"
            
            # Check forbidden patterns
            for pattern in case['should_not_contain']:
                assert pattern not in spring_el, \
                    f"{case['description']}: Forbidden pattern '{pattern}' found in: {spring_el}"

    def test_numeric_literal_parsing(self):
        """Test that numeric literals are not treated as field references."""
        test_cases = [
            {
                'sql': 'WHERE rating < 3.0',
                'expected_pattern': '#root.rating < 3.0',
                'forbidden_pattern': '#root.3.0'
            },
            {
                'sql': 'WHERE score >= 85.5 AND percentage <= 99.9',
                'expected_pattern': '85.5',
                'forbidden_pattern': '#root.85.5'
            },
            {
                'sql': 'WHERE version = 2.1 AND build_number > 1000',
                'expected_pattern': '== 2.1',
                'forbidden_pattern': '#root.2.1'
            }
        ]
        
        for case in test_cases:
            expression = parse_sql_logic(case['sql'])
            spring_el = to_spring_el(expression)
            
            assert case['expected_pattern'] in spring_el, \
                f"Expected pattern '{case['expected_pattern']}' not found in: {spring_el}"
            
            assert case['forbidden_pattern'] not in spring_el, \
                f"Forbidden pattern '{case['forbidden_pattern']}' found in: {spring_el}"

    def test_string_literal_quote_normalization(self):
        """Test that string literals are properly quoted in Spring EL."""
        test_cases = [
            {
                'sql': 'CASE WHEN status = "active" THEN "Enabled" ELSE "Disabled" END',
                'description': 'CASE with double-quoted strings',
                'should_contain': ["'active'", "'Enabled'", "'Disabled'"],
                'should_not_contain': ['"active"', '"Enabled"', '"Disabled"', "\"'", "'\""]
            },
            {
                'sql': 'WHERE description = "This is a test" AND category != "temporary"',
                'description': 'Simple string comparisons',
                'should_contain': ["'This is a test'", "'temporary'"],
                'should_not_contain': ['"This is a test"', '"temporary"']
            }
        ]
        
        for case in test_cases:
            expression = parse_sql_logic(case['sql'])
            spring_el = to_spring_el(expression)
            
            for pattern in case['should_contain']:
                assert pattern in spring_el, \
                    f"{case['description']}: Missing pattern '{pattern}' in: {spring_el}"
            
            for pattern in case['should_not_contain']:
                assert pattern not in spring_el, \
                    f"{case['description']}: Forbidden pattern '{pattern}' found in: {spring_el}"

    def test_hyphenated_field_names(self):
        """Test that hyphenated field names in brackets are properly handled."""
        test_cases = [
            {
                'sql': 'WHERE [user-profile].[age-group] IN ("25-35", "36-45")',
                'expected_spring_el': "{'25-35', '36-45'}.contains(#root.userProfile.ageGroup)"
            },
            {
                'sql': 'WHERE [employment-data].[salary-band] >= 75000',
                'expected_pattern': '#root.employmentData.salaryBand >= 75000'
            },
            {
                'sql': 'WHERE [audit-trail].[last-modified] >= "2023-06-01"',
                'expected_pattern': "#root.auditTrail.lastModified >= '2023-06-01'"
            }
        ]
        
        for case in test_cases:
            expression = parse_sql_logic(case['sql'])
            spring_el = to_spring_el(expression)
            
            if 'expected_spring_el' in case:
                assert case['expected_spring_el'] in spring_el, \
                    f"Expected exact pattern not found. Got: {spring_el}"
            
            if 'expected_pattern' in case:
                assert case['expected_pattern'] in spring_el, \
                    f"Expected pattern '{case['expected_pattern']}' not found in: {spring_el}"

    def test_ultimate_nightmare_complexity_components(self):
        """Test individual components of the ultimate nightmare complexity case."""
        components = [
            {
                'name': 'Complex IN with hyphenated fields',
                'sql': 'WHERE [user-profile].[age-group] IN ("25-35", "36-45")',
                'validation': lambda el: "{'25-35', '36-45'}.contains(#root.userProfile.ageGroup)" in el
            },
            {
                'name': 'Hyphenated field comparison',
                'sql': 'WHERE [employment-data].[salary-band] >= 75000',
                'validation': lambda el: '#root.employmentData.salaryBand >= 75000' in el
            },
            {
                'name': 'Complex NOT with parentheses',
                'sql': 'WHERE NOT ([performance-metrics].[rating] < 3.0 OR [absence-records].[days-missed] > 15)',
                'validation': lambda el: '!(' in el and '||' in el and '#root.3.0' not in el
            },
            {
                'name': 'BETWEEN with hyphenated field',
                'sql': 'WHERE contractor.[hourly-rate] BETWEEN 50 AND 150',
                'validation': lambda el: '#root.contractor.hourlyRate >= 50' in el and '#root.contractor.hourlyRate <= 150' in el
            },
            {
                'name': 'Nested CASE with hyphenated field',
                'sql': 'CASE WHEN dept.[budget-allocation] > 500000 THEN "High_Value_Employee" ELSE "Standard_Employee" END',
                'validation': lambda el: '?' in el and ':' in el and "'High_Value_Employee'" in el
            }
        ]
        
        for component in components:
            expression = parse_sql_logic(component['sql'])
            spring_el = to_spring_el(expression)
            
            assert component['validation'](spring_el), \
                f"{component['name']} validation failed. Got: {spring_el}"

    def test_full_ultimate_nightmare_complexity(self):
        """Test the complete ultimate nightmare complexity case."""
        sql = """CASE WHEN ([user-profile].[age-group] IN ('25-35', '36-45') AND [employment-data].[salary-band] >= 75000 AND NOT ([performance-metrics].[rating] < 3.0 OR [absence-records].[days-missed] > 15)) THEN CASE WHEN dept.[budget-allocation] > 500000 THEN 'High_Value_Employee' ELSE 'Standard_Employee' END WHEN contractor.[hourly-rate] BETWEEN 50 AND 150 AND proj.[deadline-pressure] = 'high' THEN 'Critical_Contractor' ELSE 'Regular_Worker' END AND ([audit-trail].[last-modified] >= '2023-06-01' OR [system-flags].[force-include] = true) AND NOT (usr.[email] LIKE '%@competitor.com' OR [security-clearance].[level] = 'restricted')"""
        
        expression = parse_sql_logic(sql)
        spring_el = to_spring_el(expression)
        
        # Comprehensive validation checks
        validations = [
            ('Contains ternary operators', lambda el: '?' in el and ':' in el),
            ('No untranslated SQL IN', lambda el: ' IN (' not in el),
            ('No untranslated SQL CASE', lambda el: 'CASE WHEN' not in el.upper()),
            ('No invalid bracket notation', lambda el: '#root.[' not in el or el.count('[') <= el.count('{')),
            ('No numeric field references', lambda el: '#root.3.0' not in el and '#root.50' not in el),
            ('Contains proper collections', lambda el: '.contains(' in el),
            ('Contains logical operators', lambda el: '&&' in el and ('||' in el or '!(' in el)),
            ('Proper string quoting', lambda el: "'" in el and ('"' not in el or el.count("'") > el.count('"')))
        ]
        
        for validation_name, validation_func in validations:
            assert validation_func(spring_el), \
                f"Ultimate complexity validation '{validation_name}' failed. Got: {spring_el[:200]}..."

    def test_edge_case_regressions(self):
        """Test that our fixes don't break existing functionality."""
        regression_cases = [
            {
                'sql': 'WHERE age > 18 AND status = "active"',
                'expected_patterns': ['#root.age > 18', "#root.status == 'active'", '&&']
            },
            {
                'sql': 'WHERE dept IN ("IT", "HR")',
                'expected_patterns': ["{'IT', 'HR'}.contains(#root.dept)"]
            },
            {
                'sql': 'WHERE salary BETWEEN 40000 AND 80000',
                'expected_patterns': ['#root.salary >= 40000', '#root.salary <= 80000', '&&']
            },
            {
                'sql': 'WHERE NOT status = "deleted"',
                'expected_patterns': ['!(#root.status', "== 'deleted')"]
            }
        ]
        
        for case in regression_cases:
            expression = parse_sql_logic(case['sql'])
            spring_el = to_spring_el(expression)
            
            for pattern in case['expected_patterns']:
                assert pattern in spring_el, \
                    f"Regression: Pattern '{pattern}' not found in: {spring_el}"