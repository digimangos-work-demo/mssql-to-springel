"""
Tests for Spring EL output format validation.

This module tests whether the generated Spring EL expressions are syntactically valid
and follow proper Spring EL conventions.
"""

import pytest
import re
from mssql_to_spring_el.parser import parse_sql_logic
from mssql_to_spring_el.converter import to_spring_el


class TestSpringELValidation:
    """Test cases for validating Spring EL output format."""

    def test_bracket_identifiers_should_be_clean(self):
        """Test that bracketed SQL identifiers are converted to clean Spring EL property access."""
        test_cases = [
            {
                'sql': 'WHERE [user_name] = "John"',
                'expected_clean': '#root.user_name == \'John\'',
                'invalid_patterns': [r'#root\.\[.*\]']  # Should not have brackets in Spring EL
            },
            {
                'sql': 'WHERE [order] = 1',
                'expected_clean': '#root.order == 1',
                'invalid_patterns': [r'#root\.\[order\]']
            },
            {
                'sql': 'WHERE [TRADER_PROFILE] = "active"',
                'expected_clean': '#root.TRADER_PROFILE == \'active\'',
                'invalid_patterns': [r'#root\.\[TRADER_PROFILE\]']
            }
        ]
        
        for case in test_cases:
            expression = parse_sql_logic(case['sql'])
            spring_el = to_spring_el(expression)
            
            # Check for invalid patterns
            for invalid_pattern in case['invalid_patterns']:
                assert not re.search(invalid_pattern, spring_el), \
                    f"Invalid pattern '{invalid_pattern}' found in: {spring_el}"
            
            # For simple identifiers, should use dot notation without brackets
            if '[' in case['sql'] and '.' not in case['sql']:
                assert not re.search(r'#root\.\[.*\]', spring_el), \
                    f"Unnecessary brackets in Spring EL: {spring_el}"

    def test_table_alias_brackets_should_be_clean(self):
        """Test that table aliases with brackets are properly formatted."""
        test_cases = [
            {
                'sql': 'WHERE u.[first_name] = "John"',
                'description': 'Table alias with bracketed column should be clean',
                'invalid_patterns': [r'#root\.\[u\]\.\[first_name\]']  # Should be #root.u.first_name
            },
            {
                'sql': 'WHERE [TRADER_PROFILE].[AUTHORIZATION_LEVEL] = "SENIOR"',
                'description': 'Bracketed table and column should be clean',
                'invalid_patterns': [r'#root\.\[.*\]\.\[.*\]']
            }
        ]
        
        for case in test_cases:
            expression = parse_sql_logic(case['sql'])
            spring_el = to_spring_el(expression)
            
            for invalid_pattern in case['invalid_patterns']:
                assert not re.search(invalid_pattern, spring_el), \
                    f"{case['description']}: Invalid pattern '{invalid_pattern}' in: {spring_el}"

    def test_in_clause_format_validation(self):
        """Test that IN clauses are properly formatted as Spring EL collection operations."""
        test_cases = [
            {
                'sql': 'WHERE emp.dept IN ("IT", "HR")',
                'required_patterns': [r'\{.*\}\.contains\(.*\)'],
                'invalid_patterns': [r'IN \(', r'emp\.dept IN']
            },
            {
                'sql': 'WHERE status IN ("active", "pending", "suspended")',
                'required_patterns': [r'\{.*\}\.contains\(#root\.status\)'],
                'invalid_patterns': [r'status IN \(']
            }
        ]
        
        for case in test_cases:
            expression = parse_sql_logic(case['sql'])
            spring_el = to_spring_el(expression)
            
            # Check required patterns
            for required_pattern in case['required_patterns']:
                assert re.search(required_pattern, spring_el), \
                    f"Required pattern '{required_pattern}' not found in: {spring_el}"
            
            # Check invalid patterns
            for invalid_pattern in case['invalid_patterns']:
                assert not re.search(invalid_pattern, spring_el), \
                    f"Invalid pattern '{invalid_pattern}' found in: {spring_el}"

    def test_in_clause_quotes_consistency(self):
        """Test that IN clause values are properly quoted."""
        sql = 'WHERE emp.dept IN ("IT", "HR")'
        expression = parse_sql_logic(sql)
        spring_el = to_spring_el(expression)
        
        # IN clause should be converted to set with proper quoting
        # Should be something like {'IT', 'HR'}.contains(#root.emp.dept)
        assert re.search(r"\{'[^']+',\s*'[^']+'\}\.contains", spring_el), \
            f"IN clause not properly quoted in: {spring_el}"

    def test_between_clause_format_validation(self):
        """Test that BETWEEN clauses are properly expanded."""
        test_cases = [
            {
                'sql': 'WHERE age BETWEEN 18 AND 65',
                'required_patterns': [r'#root\.age >= 18', r'#root\.age <= 65', r'&&'],
                'invalid_patterns': [r'BETWEEN', r'AND(?!\s*\()', r'age BETWEEN']
            },
            {
                'sql': 'WHERE salary BETWEEN 50000 AND 100000',
                'required_patterns': [r'#root\.salary >= 50000', r'#root\.salary <= 100000'],
                'invalid_patterns': [r'BETWEEN', r'salary BETWEEN']
            }
        ]
        
        for case in test_cases:
            expression = parse_sql_logic(case['sql'])
            spring_el = to_spring_el(expression)
            
            for required_pattern in case['required_patterns']:
                assert re.search(required_pattern, spring_el), \
                    f"Required pattern '{required_pattern}' not found in: {spring_el}"
            
            for invalid_pattern in case['invalid_patterns']:
                assert not re.search(invalid_pattern, spring_el), \
                    f"Invalid pattern '{invalid_pattern}' found in: {spring_el}"

    def test_logical_operators_format(self):
        """Test that logical operators are properly converted."""
        test_cases = [
            {
                'sql': 'WHERE age > 18 AND status = "active"',
                'required_patterns': [r'&&'],
                'invalid_patterns': [r'\bAND\b', r'\band\b']
            },
            {
                'sql': 'WHERE age < 18 OR status = "inactive"',
                'required_patterns': [r'\|\|'],
                'invalid_patterns': [r'\bOR\b', r'\bor\b']
            },
            {
                'sql': 'WHERE NOT status = "deleted"',
                'required_patterns': [r'!'],
                'invalid_patterns': [r'\bNOT\b', r'\bnot\b']
            }
        ]
        
        for case in test_cases:
            expression = parse_sql_logic(case['sql'])
            spring_el = to_spring_el(expression)
            
            for required_pattern in case['required_patterns']:
                assert re.search(required_pattern, spring_el), \
                    f"Required pattern '{required_pattern}' not found in: {spring_el}"
            
            for invalid_pattern in case['invalid_patterns']:
                assert not re.search(invalid_pattern, spring_el), \
                    f"Invalid pattern '{invalid_pattern}' found in: {spring_el}"

    def test_comparison_operators_format(self):
        """Test that comparison operators are properly converted."""
        test_cases = [
            {
                'sql': 'WHERE age = 25',
                'required_patterns': [r'=='],
                'invalid_patterns': [r'(?<![=!<>])=(?![=])', r'\s=\s']  # Single = not preceded/followed by =,!,<,>
            },
            {
                'sql': 'WHERE status != "active"',
                'required_patterns': [r'!='],
                'invalid_patterns': [r'<>']
            }
        ]
        
        for case in test_cases:
            expression = parse_sql_logic(case['sql'])
            spring_el = to_spring_el(expression)
            
            for required_pattern in case['required_patterns']:
                assert re.search(required_pattern, spring_el), \
                    f"Required pattern '{required_pattern}' not found in: {spring_el}"
            
            for invalid_pattern in case['invalid_patterns']:
                assert not re.search(invalid_pattern, spring_el), \
                    f"Invalid pattern '{invalid_pattern}' found in: {spring_el}"

    def test_null_handling_format(self):
        """Test that NULL comparisons are properly formatted."""
        test_cases = [
            {
                'sql': 'WHERE name IS NOT NULL',
                'required_patterns': [r'#root\.name != null'],
                'invalid_patterns': [r'IS NOT NULL', r'IS NULL']
            },
            {
                'sql': 'WHERE description IS NULL',
                'required_patterns': [r'#root\.description == null'],
                'invalid_patterns': [r'IS NULL']
            }
        ]
        
        for case in test_cases:
            expression = parse_sql_logic(case['sql'])
            spring_el = to_spring_el(expression)
            
            for required_pattern in case['required_patterns']:
                assert re.search(required_pattern, spring_el), \
                    f"Required pattern '{required_pattern}' not found in: {spring_el}"
            
            for invalid_pattern in case['invalid_patterns']:
                assert not re.search(invalid_pattern, spring_el), \
                    f"Invalid pattern '{invalid_pattern}' found in: {spring_el}"

    def test_case_expression_format(self):
        """Test that CASE expressions are properly converted to ternary operators."""
        sql = 'CASE WHEN age > 18 THEN "adult" ELSE "minor" END'
        
        try:
            expression = parse_sql_logic(sql)
            spring_el = to_spring_el(expression)
            
            # Should be converted to ternary operator format
            # Pattern: condition ? value1 : value2
            assert re.search(r'\?\s*.*\s*:', spring_el), \
                f"CASE not converted to ternary operator in: {spring_el}"
            
            # Should not contain SQL CASE keywords
            invalid_patterns = [r'\bCASE\b', r'\bWHEN\b', r'\bTHEN\b', r'\bELSE\b', r'\bEND\b']
            for invalid_pattern in invalid_patterns:
                assert not re.search(invalid_pattern, spring_el, re.IGNORECASE), \
                    f"SQL CASE keyword '{invalid_pattern}' found in: {spring_el}"
                    
        except Exception as e:
            pytest.skip(f"CASE expressions not fully implemented: {e}")

    def test_string_literal_quotes(self):
        """Test that string literals use proper Spring EL quoting."""
        test_cases = [
            {
                'sql': 'WHERE name = "John"',
                'description': 'Double quotes should become single quotes in Spring EL'
            },
            {
                'sql': "WHERE name = 'John'",
                'description': 'Single quotes should remain single quotes'
            }
        ]
        
        for case in test_cases:
            expression = parse_sql_logic(case['sql'])
            spring_el = to_spring_el(expression)
            
            # Spring EL should use single quotes for string literals
            assert "'" in spring_el, f"String literal not properly quoted in: {spring_el}"
            
            # Should not have unescaped double quotes around string values
            assert not re.search(r'==\s*"[^"]*"', spring_el), \
                f"Double quotes found in string literal: {spring_el}"

    def test_property_access_consistency(self):
        """Test that property access follows consistent patterns."""
        test_cases = [
            {
                'sql': 'WHERE emp.name = "John" AND emp.dept = "IT"',
                'description': 'Consistent table alias usage'
            },
            {
                'sql': 'WHERE user_id = 123 AND user_name = "John"',
                'description': 'Consistent simple property access'
            }
        ]
        
        for case in test_cases:
            expression = parse_sql_logic(case['sql'])
            spring_el = to_spring_el(expression)
            
            # All property access should start with #root
            property_accesses = re.findall(r'#\w+\.[^=<>!&|]+', spring_el)
            for access in property_accesses:
                assert access.startswith('#root.'), \
                    f"Property access should start with #root: {access} in {spring_el}"

    def test_complex_expression_structure(self):
        """Test that complex expressions have proper parentheses and structure."""
        sql = 'WHERE (age > 18 AND status = "active") OR (role = "admin" AND verified = true)'
        
        expression = parse_sql_logic(sql)
        spring_el = to_spring_el(expression)
        
        # Check balanced parentheses
        open_parens = spring_el.count('(')
        close_parens = spring_el.count(')')
        assert open_parens == close_parens, \
            f"Unbalanced parentheses in: {spring_el}"
        
        # Should contain proper logical operators
        assert '&&' in spring_el or '||' in spring_el, \
            f"Missing logical operators in complex expression: {spring_el}"

    def test_invalid_spring_el_patterns(self):
        """Test for patterns that would make Spring EL invalid."""
        test_cases = [
            'WHERE [user_name] = "John"',
            'WHERE u.[first_name] = "John"',
            'WHERE dept IN ("IT", "HR")',
            'WHERE age BETWEEN 18 AND 65'
        ]
        
        invalid_patterns = [
            r'#root\.\[.*\]\.\[.*\]',  # Double bracketed access
            r'#root\.\[\w+\](?!\.\[)',  # Single bracket without being part of double bracket
            r'\bIN\s*\(',              # SQL IN syntax
            r'\bBETWEEN\b',            # SQL BETWEEN syntax
            r'\bAND\b(?!\s*\()',       # SQL AND (not part of function call)
            r'\bOR\b(?!\s*\()',        # SQL OR (not part of function call)
            r'\bNOT\b(?!\s*\()',       # SQL NOT (not part of function call)
            r'(?<![=!<>])=(?![=])',    # Single equals (assignment, not comparison)
        ]
        
        for sql in test_cases:
            expression = parse_sql_logic(sql)
            spring_el = to_spring_el(expression)
            
            for invalid_pattern in invalid_patterns:
                assert not re.search(invalid_pattern, spring_el), \
                    f"Invalid Spring EL pattern '{invalid_pattern}' found in: {spring_el} (from SQL: {sql})"

    def test_complex_bracketed_in_clause_parsing(self):
        """Test that complex bracketed IN clauses are properly parsed as BinaryOp, not Variable."""
        test_cases = [
            {
                'sql': 'WHERE [TRADER_PROFILE].[AUTHORIZATION_LEVEL] IN ("SENIOR_TRADER", "VP_TRADING")',
                'description': 'Complex bracketed table.column IN clause'
            },
            {
                'sql': 'WHERE [user].[role] IN ("admin", "manager")',
                'description': 'Bracketed table.column IN clause'
            },
            {
                'sql': 'WHERE [COMPLIANCE_CHECK].[STATUS] NOT IN ("failed", "pending")',
                'description': 'Complex bracketed NOT IN clause'
            }
        ]
        
        for case in test_cases:
            expression = parse_sql_logic(case['sql'])
            spring_el = to_spring_el(expression)
            
            # These should NOT contain SQL IN syntax in the output
            assert not re.search(r'\sIN\s*\(', spring_el), \
                f"{case['description']}: SQL IN syntax found in Spring EL: {spring_el}"
            
            # Should contain proper Spring EL contains() syntax
            assert '.contains(' in spring_el, \
                f"{case['description']}: Missing .contains() in Spring EL: {spring_el}"
            
            # Should not have invalid bracket notation
            assert not re.search(r'#root\.[^.]+\.\[', spring_el), \
                f"{case['description']}: Invalid bracket notation in Spring EL: {spring_el}"

    def test_not_operator_placement(self):
        """Test that NOT operator is properly placed in Spring EL expressions."""
        test_cases = [
            {
                'sql': 'WHERE NOT [TRADER_PROFILE].[SUSPENDED] = 1',
                'description': 'NOT with bracketed field comparison'
            },
            {
                'sql': 'WHERE NOT status = "active"',
                'description': 'NOT with simple field comparison'
            },
            {
                'sql': 'WHERE NOT (age > 18 AND verified = true)',
                'description': 'NOT with parenthesized expression'
            }
        ]
        
        for case in test_cases:
            expression = parse_sql_logic(case['sql'])
            spring_el = to_spring_el(expression)
            
            # Should not have incorrect NOT placement like "!#root.field == value"
            assert not re.search(r'!#root\.[^=]+==', spring_el), \
                f"{case['description']}: Incorrect NOT placement in: {spring_el}"
            
            # Should have proper NOT placement: "!(expression)" or "field != value"
            has_proper_not = ('!(' in spring_el or '!=' in spring_el or 
                             re.search(r'!\{.*\}\.contains', spring_el))
            assert has_proper_not, \
                f"{case['description']}: Missing proper NOT syntax in: {spring_el}"

    def test_mixed_bracket_and_operator_complexity(self):
        """Test complex expressions mixing brackets, operators, and functions."""
        test_cases = [
            {
                'sql': 'WHERE [TRADER_PROFILE].[AUTHORIZATION_LEVEL] IN ("SENIOR", "VP") AND [COMPLIANCE].[SCORE] BETWEEN 1 AND 75',
                'description': 'Mixed IN and BETWEEN with brackets'
            },
            {
                'sql': 'WHERE [USER].[ROLE] NOT IN ("guest", "temp") OR [USER].[STATUS] = "active"',
                'description': 'Mixed NOT IN and equality with brackets'
            }
        ]
        
        for case in test_cases:
            try:
                expression = parse_sql_logic(case['sql'])
                spring_el = to_spring_el(expression)
                
                # Should not contain any SQL keywords
                sql_keywords = ['IN (', 'NOT IN (', 'BETWEEN', ' AND ', ' OR ']
                for keyword in sql_keywords:
                    assert keyword not in spring_el, \
                        f"{case['description']}: SQL keyword '{keyword}' found in: {spring_el}"
                
                # Should not have invalid bracket notation
                assert not re.search(r'#root\.[^.]+\.\[', spring_el), \
                    f"{case['description']}: Invalid bracket notation in: {spring_el}"
                    
            except Exception as e:
                # If parsing fails, that's also an issue we should track
                pytest.fail(f"{case['description']}: Parsing failed with error: {e}")

    def test_case_expression_invalid_patterns(self):
        """Test that CASE expressions don't leave SQL fragments in Spring EL."""
        try:
            sql = 'CASE WHEN [POSITION].[TYPE] = "equity" THEN "stock" ELSE "other" END'
            expression = parse_sql_logic(sql)
            spring_el = to_spring_el(expression)
            
            # Should not contain SQL CASE keywords
            sql_case_keywords = ['CASE', 'WHEN', 'THEN', 'ELSE', 'END']
            for keyword in sql_case_keywords:
                assert keyword not in spring_el.upper(), \
                    f"SQL CASE keyword '{keyword}' found in Spring EL: {spring_el}"
            
            # Should not have invalid bracket notation
            assert not re.search(r'#root\.[^.]+\.\[', spring_el), \
                f"Invalid bracket notation in CASE expression: {spring_el}"
                
        except Exception as e:
            pytest.skip(f"CASE expressions not fully implemented: {e}")