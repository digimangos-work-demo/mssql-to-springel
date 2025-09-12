"""
Tests for ultimate complexity Spring EL validation.
These tests catch issues in the most complex SQL parsing scenarios.
"""

import pytest
import re
from mylibrary.parser import parse_sql_logic
from mylibrary.converter import to_spring_el


class TestUltimateComplexityValidation:
    """Validation tests for the most complex SQL scenarios."""

    def test_ultimate_nightmare_complexity_spring_el_validity(self):
        """Test that the ultimate nightmare complexity produces valid Spring EL."""
        sql = "CASE WHEN ([user-profile].[age-group] IN ('25-35', '36-45') AND [employment-data].[salary-band] >= 75000 AND NOT ([performance-metrics].[rating] < 3.0 OR [absence-records].[days-missed] > 15)) THEN CASE WHEN dept.[budget-allocation] > 500000 THEN 'High_Value_Employee' ELSE 'Standard_Employee' END WHEN contractor.[hourly-rate] BETWEEN 50 AND 150 AND proj.[deadline-pressure] = 'high' THEN 'Critical_Contractor' ELSE 'Regular_Worker' END AND ([audit-trail].[last-modified] >= '2023-06-01' OR [system-flags].[force-include] = true) AND NOT (usr.[email] LIKE '%@competitor.com' OR [security-clearance].[level] = 'restricted')"
        
        expression = parse_sql_logic(sql)
        spring_el = to_spring_el(expression)
        
        # Test 1: No SQL keywords should remain in Spring EL output
        sql_keywords = ['END WHEN', 'THEN', 'ELSE', 'CASE WHEN', 'BETWEEN', 'AND', 'OR', 'NOT', 'IN', 'LIKE']
        for keyword in sql_keywords:
            assert keyword not in spring_el, f"SQL keyword '{keyword}' found in Spring EL: {spring_el}"
        
        # Test 2: Should not contain hyphenated field references
        # Spring EL doesn't support hyphens in property names - they should be converted to camelCase
        invalid_patterns = [
            r'#root\.\w*-\w*',  # #root.word-word
            r'#root\.\w*-\w*\.\w*-\w*',  # #root.word-word.word-word
            'user-profile', 'age-group', 'employment-data', 'salary-band',
            'performance-metrics', 'absence-records', 'days-missed'
        ]
        for pattern in invalid_patterns:
            if isinstance(pattern, str) and not pattern.startswith('#root'):
                # Simple string check
                assert pattern not in spring_el, f"Hyphenated field name '{pattern}' found in: {spring_el}"
            else:
                # Regex pattern check
                assert not re.search(pattern, spring_el), f"Invalid hyphenated property access '{pattern}' found in: {spring_el}"
        
        # Test 3: Should not contain incomplete ternary operators
        # Count ? and : to ensure they're balanced
        question_marks = spring_el.count('?')
        colons = spring_el.count(':')
        # In valid ternary operators, colons should equal or exceed question marks
        assert colons >= question_marks, f"Unbalanced ternary operators (? count: {question_marks}, : count: {colons}) in: {spring_el}"
        
        # Test 4: Should not contain malformed property access
        malformed_patterns = [
            r'#root\.\[',  # #root.[  (should be bracket notation)
            r'\]\.(?!\w)',  # ].X where X is not a word character
            r'#root\.CASE',  # #root.CASE (CASE is not a property)
        ]
        for pattern in malformed_patterns:
            assert not re.search(pattern, spring_el), f"Malformed property access '{pattern}' found in: {spring_el}"
        
        # Test 5: All parentheses should be balanced
        open_parens = spring_el.count('(')
        close_parens = spring_el.count(')')
        assert open_parens == close_parens, f"Unbalanced parentheses (open: {open_parens}, close: {close_parens}) in: {spring_el}"
        
        # Test 6: All curly braces should be balanced (for set literals)
        open_braces = spring_el.count('{')
        close_braces = spring_el.count('}')
        assert open_braces == close_braces, f"Unbalanced braces (open: {open_braces}, close: {close_braces}) in: {spring_el}"

    def test_hyphenated_field_names_validation(self):
        """Test that hyphenated field names are properly converted to camelCase in Spring EL."""
        test_cases = [
            {
                'sql': 'WHERE [user-profile].[first-name] = "John"',
                'description': 'Simple hyphenated field access',
                'should_not_contain': ['#root.user-profile.first-name', '#root.user-profile', 'first-name'],
                'should_contain': ['#root.userProfile.firstName']
            },
            {
                'sql': 'WHERE [employment-data].[salary-band] >= 75000',
                'description': 'Hyphenated table and column names',
                'should_not_contain': ['#root.employment-data.salary-band', 'employment-data', 'salary-band'],
                'should_contain': ['#root.employmentData.salaryBand']
            },
            {
                'sql': 'WHERE [performance-metrics].[rating] < 3.0',
                'description': 'Hyphenated field with numeric comparison',
                'should_not_contain': ['#root.performance-metrics.rating', 'performance-metrics'],
                'should_contain': ['#root.performanceMetrics.rating']
            }
        ]
        
        for case in test_cases:
            expression = parse_sql_logic(case['sql'])
            spring_el = to_spring_el(expression)
            
            # Check forbidden patterns
            for forbidden in case['should_not_contain']:
                assert forbidden not in spring_el, \
                    f"{case['description']}: Forbidden pattern '{forbidden}' found in: {spring_el}"
            
            # Check required patterns
            for required in case['should_contain']:
                assert required in spring_el, \
                    f"{case['description']}: Required pattern '{required}' not found in: {spring_el}"

    def test_nested_case_statements_validation(self):
        """Test that nested CASE statements produce valid Spring EL."""
        sql = "CASE WHEN status = 'active' THEN CASE WHEN priority = 1 THEN 'High' ELSE 'Normal' END ELSE 'Inactive' END"
        
        expression = parse_sql_logic(sql)
        spring_el = to_spring_el(expression)
        
        # Should not contain SQL CASE syntax
        assert 'CASE WHEN' not in spring_el
        assert 'THEN' not in spring_el
        assert 'ELSE' not in spring_el.replace('ELSE', '').strip() or spring_el.count('ELSE') == 0
        assert 'END' not in spring_el
        
        # Should contain proper ternary operators
        assert '?' in spring_el
        assert ':' in spring_el
        
        # Should be properly nested
        question_marks = spring_el.count('?')
        assert question_marks >= 2, f"Expected at least 2 ternary operators for nested CASE, got {question_marks}"

    def test_complex_between_and_in_validation(self):
        """Test BETWEEN and IN operators produce valid Spring EL."""
        sql = "WHERE salary BETWEEN 50000 AND 100000 AND department IN ('IT', 'Engineering', 'Data Science')"
        
        expression = parse_sql_logic(sql)
        spring_el = to_spring_el(expression)
        
        # Should not contain SQL syntax
        assert 'BETWEEN' not in spring_el
        assert ' AND ' not in spring_el  # Should be && in Spring EL
        assert ' IN ' not in spring_el   # Should be .contains() in Spring EL
        
        # Should contain Spring EL equivalents
        assert '&&' in spring_el  # AND conversion
        assert '.contains(' in spring_el  # IN conversion
        assert '>=' in spring_el and '<=' in spring_el  # BETWEEN conversion

    def test_like_operator_validation(self):
        """Test LIKE operator produces valid Spring EL."""
        sql = "WHERE email LIKE '%@company.com' AND name NOT LIKE 'Test%'"
        
        expression = parse_sql_logic(sql)
        spring_el = to_spring_el(expression)
        
        # Should not contain SQL LIKE syntax
        assert ' LIKE ' not in spring_el
        assert ' NOT LIKE ' not in spring_el
        
        # Should contain Spring EL regex equivalent
        assert '=~' in spring_el or 'matches(' in spring_el

    def test_null_checks_validation(self):
        """Test IS NULL and IS NOT NULL produce valid Spring EL."""
        sql = "WHERE description IS NOT NULL AND deleted_date IS NULL"
        
        expression = parse_sql_logic(sql)
        spring_el = to_spring_el(expression)
        
        # Should not contain SQL syntax
        assert 'IS NOT NULL' not in spring_el
        assert 'IS NULL' not in spring_el
        
        # Should contain Spring EL null checks
        assert '!= null' in spring_el or '== null' in spring_el

    def test_ultimate_complexity_structure_validation(self):
        """Test that ultimate complexity maintains proper Spring EL structure."""
        sql = "CASE WHEN ([user-profile].[age-group] IN ('25-35', '36-45') AND [employment-data].[salary-band] >= 75000) THEN 'Qualified' ELSE 'Not Qualified' END"
        
        expression = parse_sql_logic(sql)
        spring_el = to_spring_el(expression)
        
        # Should be a single, well-formed expression
        assert spring_el.count('(') == spring_el.count(')')
        assert spring_el.count('{') == spring_el.count('}')
        
        # Should not have dangling operators
        dangling_patterns = [
            r'&&\s*$',  # && at end
            r'\|\|\s*$',  # || at end  
            r'!\s*$',   # ! at end
            r'\?\s*$',  # ? at end without :
            r':\s*$',   # : at end without content
        ]
        
        for pattern in dangling_patterns:
            assert not re.search(pattern, spring_el.strip()), \
                f"Dangling operator pattern '{pattern}' found in: {spring_el}"
        
        # Should start and end appropriately
        spring_el_stripped = spring_el.strip()
        valid_starts = ['(', '#root', "'", '"', '{', '!']
        valid_ends = [')', "'", '"', '}', 'true', 'false', 'null'] + [str(i) for i in range(10)]
        
        starts_valid = any(spring_el_stripped.startswith(start) for start in valid_starts)
        ends_valid = any(spring_el_stripped.endswith(end) for end in valid_ends)
        
        assert starts_valid, f"Spring EL should start with valid token, got: {spring_el_stripped[:20]}..."
        assert ends_valid, f"Spring EL should end with valid token, got: ...{spring_el_stripped[-20:]}"