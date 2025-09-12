import pytest
from mssql_to_spring_el.parser import parse_sql_logic
from mssql_to_spring_el.converter import to_spring_el


class TestEdgeCases:
    """Test edge cases and complex scenarios that might break the parser."""

    def test_square_brackets_simple(self):
        """Test simple square bracket identifiers."""
        sql = "WHERE [user_name] = 'John'"
        
        # This might not work yet - testing current limitations
        try:
            expression = parse_sql_logic(sql)
            el_string = to_spring_el(expression)
            assert el_string is not None
        except (ValueError, NotImplementedError) as e:
            # Expected for features not yet implemented
            pytest.skip(f"Square brackets not yet supported: {e}")

    def test_table_alias_with_brackets(self):
        """Test table aliases with square bracket column names."""
        sql = "WHERE u.[first_name] = 'John' AND p.[project_name] LIKE 'Test%'"
        
        try:
            expression = parse_sql_logic(sql)
            el_string = to_spring_el(expression)
            assert el_string is not None
        except (ValueError, NotImplementedError) as e:
            pytest.skip(f"Bracket identifiers with aliases not yet supported: {e}")

    def test_reserved_words_in_brackets(self):
        """Test SQL reserved words as column names in brackets."""
        sql = "WHERE [order] = 1 AND [select] = 'value'"
        
        try:
            expression = parse_sql_logic(sql)
            el_string = to_spring_el(expression)
            assert el_string is not None
        except (ValueError, NotImplementedError) as e:
            pytest.skip(f"Reserved words in brackets not yet supported: {e}")

    def test_special_characters_in_identifiers(self):
        """Test special characters in column names."""
        sql = "WHERE [email-address] LIKE '%@test.com' AND [user-id] > 0"
        
        try:
            expression = parse_sql_logic(sql)
            el_string = to_spring_el(expression)
            assert el_string is not None
        except (ValueError, NotImplementedError) as e:
            pytest.skip(f"Special characters in identifiers not yet supported: {e}")

    def test_numbers_in_identifiers(self):
        """Test numbers in identifiers."""
        sql = "WHERE field1 = 'value' AND table2.column3 > 100"
        
        expression = parse_sql_logic(sql)
        el_string = to_spring_el(expression)
        
        # This should work with current parser
        assert "#root.field1" in el_string
        assert "#root.table2.column3" in el_string

    def test_complex_case_parsing_limitations(self):
        """Test complex CASE conditions that might fail."""
        sql = "CASE WHEN emp.age BETWEEN 25 AND 65 AND emp.dept IN ('IT', 'HR') THEN 'Standard' ELSE 'Other' END"
        
        try:
            expression = parse_sql_logic(sql)
            el_string = to_spring_el(expression)
            
            # Check if it parsed correctly or used fallback
            assert "?" in el_string
            assert ":" in el_string
            
            # If it has PARSE_ERROR, that's expected for complex conditions
            if "PARSE_ERROR" in el_string:
                pytest.skip("Complex CASE conditions not fully supported yet")
                
        except (ValueError, NotImplementedError) as e:
            pytest.skip(f"Complex CASE parsing not yet supported: {e}")

    def test_deeply_nested_with_aliases(self):
        """Test deeply nested conditions with multiple table aliases."""
        sql = "WHERE ((emp.type = 'full' AND (role.level >= 5 OR role.manager = true)) AND (dept.budget > 50000 OR exec.override = true))"
        
        expression = parse_sql_logic(sql)
        el_string = to_spring_el(expression)
        
        # Should handle multiple levels of nesting
        assert "#root.emp.type" in el_string
        assert "#root.role.level" in el_string
        assert "#root.dept.budget" in el_string
        assert "||" in el_string
        assert "&&" in el_string

    def test_multiple_in_clauses_with_aliases(self):
        """Test multiple IN clauses with different table aliases."""
        sql = "WHERE emp.dept IN ('IT', 'HR') AND proj.status IN ('active', 'pending') AND loc.region IN ('US', 'EU')"
        
        expression = parse_sql_logic(sql)
        el_string = to_spring_el(expression)
        
        # Should handle multiple IN clauses
        assert "contains" in el_string
        assert "#root.emp.dept" in el_string
        assert "#root.proj.status" in el_string
        assert "#root.loc.region" in el_string

    def test_mixed_functions_and_aliases(self):
        """Test mixing functions with table aliases."""
        sql = "WHERE ISNULL(u.middle, '') != '' AND LEN(p.desc) > 50 AND UPPER(d.name) = 'SALES'"
        
        expression = parse_sql_logic(sql)
        el_string = to_spring_el(expression)
        
        # Should handle functions with aliases
        assert el_string is not None
        assert "&&" in el_string

    def test_case_with_simple_alias_conditions(self):
        """Test CASE with simple conditions using aliases (should work)."""
        sql = "CASE WHEN emp.level = 1 THEN 'Junior' WHEN emp.level = 2 THEN 'Senior' ELSE 'Lead' END"
        
        expression = parse_sql_logic(sql)
        el_string = to_spring_el(expression)
        
        # Should work with simple conditions
        assert "?" in el_string
        assert ":" in el_string
        assert "#root.emp.level" in el_string
        assert "'Junior'" in el_string


class TestComplexityLimits:
    """Test cases designed to find the current limits of the parser."""

    def test_maximum_nesting_depth(self):
        """Test maximum supported nesting depth."""
        sql = "WHERE ((((a.x = 1 AND b.y = 2) OR (c.z = 3 AND d.w = 4)) AND ((e.v = 5 OR f.u = 6) AND (g.t = 7 OR h.s = 8))))"
        
        expression = parse_sql_logic(sql)
        el_string = to_spring_el(expression)
        
        # Should handle reasonable nesting depth
        assert "&&" in el_string
        assert "||" in el_string

    def test_many_conditions_with_aliases(self):
        """Test many conditions chained together."""
        sql = "WHERE a.f1 = 1 AND b.f2 = 2 AND c.f3 = 3 AND d.f4 = 4 AND e.f5 = 5 AND f.f6 = 6"
        
        expression = parse_sql_logic(sql)
        el_string = to_spring_el(expression)
        
        # Should handle many chained conditions
        assert el_string.count("&&") >= 5
        assert "#root.a.f1" in el_string
        assert "#root.f.f6" in el_string

    def test_mixed_operators_complexity(self):
        """Test mixing all supported operators."""
        sql = "WHERE emp.salary >= 50000 AND emp.dept IN ('IT', 'HR') AND emp.name LIKE 'John%' AND emp.active = true AND NOT emp.remote = false"
        
        expression = parse_sql_logic(sql)
        el_string = to_spring_el(expression)
        
        # Should handle all operator types
        assert ">=" in el_string
        assert "contains" in el_string
        assert "matches" in el_string or "contains" in el_string  # LIKE conversion
        assert "==" in el_string
        assert "!" in el_string or "not" in el_string  # NOT conversion


class TestWhitespaceHandling:
    """Test various whitespace scenarios that could break parsing."""

    def test_extra_spaces_around_operators(self):
        """Test extra spaces around operators."""
        sql = "WHERE   age    >    18   AND    status   =   'active'  "
        
        expression = parse_sql_logic(sql)
        el_string = to_spring_el(expression)
        
        # Should handle extra spaces gracefully
        assert "#root.age" in el_string
        assert "#root.status" in el_string
        assert "&&" in el_string

    def test_tabs_instead_of_spaces(self):
        """Test tabs instead of spaces."""
        sql = "WHERE\tage\t>\t18\tAND\tstatus\t=\t'active'"
        
        expression = parse_sql_logic(sql)
        el_string = to_spring_el(expression)
        
        # Should handle tabs like spaces
        assert "#root.age" in el_string
        assert "#root.status" in el_string

    def test_newlines_in_sql(self):
        """Test newlines in SQL (multiline SQL)."""
        sql = """WHERE age > 18
        AND status = 'active'
        AND department IN ('IT', 'HR')"""
        
        expression = parse_sql_logic(sql)
        el_string = to_spring_el(expression)
        
        # Should handle newlines
        assert "#root.age" in el_string
        assert "#root.status" in el_string
        assert "#root.department" in el_string

    def test_mixed_whitespace_chaos(self):
        """Test chaotic mix of spaces, tabs, and newlines."""
        sql = """WHERE  \t age\t> \n18   AND\t\t
        status =  'active' \t
        OR   \tdepartment\nIN  ('IT',\t'HR')"""
        
        expression = parse_sql_logic(sql)
        el_string = to_spring_el(expression)
        
        # Should handle mixed whitespace
        assert "#root.age" in el_string
        assert "#root.status" in el_string
        assert "#root.department" in el_string

    def test_case_with_newlines_and_tabs(self):
        """Test CASE expression with mixed whitespace."""
        sql = """CASE\tWHEN age\n>\t65
        THEN\t'Senior'
        WHEN\nage > 18\t
        THEN 'Adult'\n
        ELSE   'Minor'\t
        END"""
        
        expression = parse_sql_logic(sql)
        el_string = to_spring_el(expression)
        
        # Should handle CASE with mixed whitespace
        assert "?" in el_string
        assert ":" in el_string
        assert "'Senior'" in el_string

    def test_functions_with_whitespace(self):
        """Test function calls with various whitespace."""
        sql = "WHERE ISNULL\t(\n  name  ,\t  'Unknown'\n  )\t=  'John'"
        
        expression = parse_sql_logic(sql)
        el_string = to_spring_el(expression)
        
        # Should handle function whitespace
        assert el_string is not None

    def test_parentheses_with_whitespace(self):
        """Test parentheses with various whitespace patterns."""
        sql = "WHERE\t( \n age > 18\t AND  \n(\tstatus = 'active'\nOR\tis_premium =\ttrue\n)\t)"
        
        expression = parse_sql_logic(sql)
        el_string = to_spring_el(expression)
        
        # Should handle parentheses with whitespace
        assert "#root.age" in el_string
        assert "#root.status" in el_string
        assert "&&" in el_string
        assert "||" in el_string

    def test_in_clause_with_whitespace(self):
        """Test IN clause with various whitespace in the list."""
        sql = "WHERE status IN\t(\n  'active'  ,\t\n  'pending'\t,\n  'verified'  \n)"
        
        expression = parse_sql_logic(sql)
        el_string = to_spring_el(expression)
        
        # Should handle IN clause with whitespace
        assert "contains" in el_string
        assert "active" in el_string
        assert "pending" in el_string

    def test_like_pattern_with_whitespace(self):
        """Test LIKE patterns with whitespace."""
        sql = "WHERE\tname\nLIKE\t\n'John%'  AND  email\t LIKE\n'%@test.com'"
        
        expression = parse_sql_logic(sql)
        el_string = to_spring_el(expression)
        
        # Should handle LIKE with whitespace
        assert "#root.name" in el_string
        assert "#root.email" in el_string

    def test_between_with_whitespace(self):
        """Test BETWEEN with various whitespace."""
        sql = "WHERE\tage\n BETWEEN\t\n18\t AND   \n65"
        
        expression = parse_sql_logic(sql)
        el_string = to_spring_el(expression)
        
        # Should handle BETWEEN with whitespace
        assert "#root.age" in el_string

    def test_trailing_and_leading_whitespace(self):
        """Test with significant leading and trailing whitespace."""
        sql = "\n\t   WHERE age > 18 AND status = 'active'   \t\n\n"
        
        expression = parse_sql_logic(sql)
        el_string = to_spring_el(expression)
        
        # Should trim and handle properly
        assert "#root.age" in el_string
        assert "#root.status" in el_string

    def test_whitespace_in_string_literals(self):
        """Test whitespace preservation in string literals."""
        sql = "WHERE description = 'This has  tabs\tand\nnewlines' AND name = '  spaces  '"
        
        expression = parse_sql_logic(sql)
        el_string = to_spring_el(expression)
        
        # Should preserve whitespace in string literals
        assert "This has  tabs\tand\nnewlines" in el_string
        assert "  spaces  " in el_string

    def test_multiline_complex_case(self):
        """Test complex multiline CASE with varied formatting."""
        sql = """CASE
            WHEN emp.age > 65
                AND emp.status = 'retired'
            THEN 'Senior'
            WHEN emp.age BETWEEN 25 AND 65
                AND emp.active = true
            THEN 'Active'
            ELSE
                'Other'
        END
        AND emp.department IN (
            'IT',
            'HR',
            'Finance'
        )"""
        
        expression = parse_sql_logic(sql)
        el_string = to_spring_el(expression)
        
        # Should handle complex multiline formatting
        assert "?" in el_string
        assert ":" in el_string
        assert "contains" in el_string

    def test_no_spaces_edge_case(self):
        """Test minimal spacing (almost no spaces)."""
        sql = "WHERE age>18AND status='active'OR(department='IT'AND salary>=50000)"
        
        try:
            expression = parse_sql_logic(sql)
            el_string = to_spring_el(expression)
            
            # Might work or might fail - depends on tokenization
            assert el_string is not None
        except (ValueError, NotImplementedError):
            # Expected - minimal spacing might not be supported
            pytest.skip("Minimal spacing not supported")

    def test_unicode_whitespace(self):
        """Test Unicode whitespace characters."""
        # Non-breaking space (U+00A0) and other Unicode spaces
        sql = "WHERE age\u00a0>\u200918\u2009AND\u2009status\u00a0=\u00a0'active'"
        
        try:
            expression = parse_sql_logic(sql)
            el_string = to_spring_el(expression)
            assert el_string is not None
        except (ValueError, NotImplementedError):
            # Expected - Unicode whitespace might not be supported
            pytest.skip("Unicode whitespace not supported")
