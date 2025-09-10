#!/usr/bin/env python3
"""
Test the immediate whitespace fixes from the IMMEDIATE_FIXES plan.
"""

import pytest
from mylibrary.parser import parse_sql_logic, _normalize_whitespace
from mylibrary.converter import to_spring_el


class TestImmediateWhitespaceFixes:
    """Test cases to verify the immediate whitespace fixes are working."""
    
    def test_whitespace_normalization_function(self):
        """Test the _normalize_whitespace function directly."""
        
        # Test tab normalization
        sql = "WHERE\tage\t>\t18\tAND\tstatus\t=\t'active'"
        normalized = _normalize_whitespace(sql)
        assert normalized == "WHERE age > 18 AND status = 'active'"
        
        # Test newline normalization
        sql = "WHERE age > 18\nAND status = 'active'"
        normalized = _normalize_whitespace(sql)
        assert normalized == "WHERE age > 18 AND status = 'active'"
        
        # Test mixed whitespace
        sql = "WHERE   age    >    18   AND    status   =   'active'"
        normalized = _normalize_whitespace(sql)
        assert normalized == "WHERE age > 18 AND status = 'active'"
        
        # Test string literal preservation
        sql = "WHERE description = 'Has  multiple   spaces' AND comment = '  trimmed  '"
        normalized = _normalize_whitespace(sql)
        assert "'Has  multiple   spaces'" in normalized
        assert "'  trimmed  '" in normalized
    
    def test_tab_handling_end_to_end(self):
        """Test tabs work end-to-end from parsing to Spring EL."""
        sql = "WHERE\tage\t>\t18\tAND\tstatus\t=\t'active'"
        expression = parse_sql_logic(sql)
        spring_el = to_spring_el(expression)
        
        assert "#root.age" in spring_el
        assert "#root.status" in spring_el
        assert "&&" in spring_el
        assert "'active'" in spring_el
    
    def test_newline_handling_end_to_end(self):
        """Test newlines work end-to-end from parsing to Spring EL."""
        sql = """WHERE age > 18
AND status = 'active'"""
        expression = parse_sql_logic(sql)
        spring_el = to_spring_el(expression)
        
        assert "#root.age > 18" in spring_el
        assert "#root.status == 'active'" in spring_el
        assert "&&" in spring_el
    
    def test_case_with_newlines(self):
        """Test CASE expressions with newlines work."""
        sql = """CASE
WHEN age > 65 THEN 'Senior'
WHEN age > 18 THEN 'Adult'
ELSE 'Minor'
END"""
        expression = parse_sql_logic(sql)
        spring_el = to_spring_el(expression)
        
        assert "?" in spring_el  # Ternary operator
        assert "'Senior'" in spring_el
        assert "'Adult'" in spring_el
        assert "'Minor'" in spring_el
    
    def test_function_with_multiline_formatting(self):
        """Test function calls with multiline formatting."""
        sql = """ISNULL(
  name,
  'Unknown'
) = 'John'"""
        expression = parse_sql_logic(sql)
        spring_el = to_spring_el(expression)
        
        assert "ISNULL" in spring_el or "name ?" in spring_el  # Either function call or ternary
        assert "'Unknown'" in spring_el
        assert "'John'" in spring_el
    
    def test_complex_mixed_whitespace(self):
        """Test complex case with mixed tabs, newlines, and spaces."""
        sql = """WHERE\tage > 18
    AND\tstatus = 'active'
    OR\tdepartment\tIN\t('IT', 'HR')"""
        expression = parse_sql_logic(sql)
        spring_el = to_spring_el(expression)
        
        assert "#root.age > 18" in spring_el
        assert "#root.status == 'active'" in spring_el
        assert "contains" in spring_el  # IN operator
        assert ("'IT'" in spring_el and "'HR'" in spring_el) or ("IT" in spring_el and "HR" in spring_el)  # Either quoted or unquoted is fine
    
    def test_preserved_string_whitespace(self):
        """Test that whitespace in string literals is preserved exactly."""
        sql = "WHERE description = 'This has  multiple   spaces' AND comment = '  Leading and trailing  '"
        expression = parse_sql_logic(sql)
        spring_el = to_spring_el(expression)
        
        # The exact strings should be preserved
        assert "'This has  multiple   spaces'" in spring_el
        assert "'  Leading and trailing  '" in spring_el


def test_immediate_fixes_summary():
    """Summary test showing overall improvement from immediate fixes."""
    
    test_cases = [
        # Tab handling
        ("WHERE\tage\t>\t18\tAND\tstatus\t=\t'active'", "Basic tab handling"),
        
        # Newline handling  
        ("WHERE age > 18\nAND status = 'active'", "Basic newline handling"),
        
        # CASE with whitespace
        ("CASE\nWHEN age > 65 THEN 'Senior'\nELSE 'Other'\nEND", "CASE with newlines"),
        
        # Function with whitespace
        ("ISNULL(\n  name,\n  'Unknown'\n) = 'John'", "Function with formatting"),
        
        # Mixed whitespace chaos
        ("WHERE\tage > 18\n    AND\tstatus = 'active'", "Mixed whitespace"),
    ]
    
    passed = 0
    failed = 0
    
    for sql, description in test_cases:
        try:
            expression = parse_sql_logic(sql)
            spring_el = to_spring_el(expression)
            
            # Basic validation - must contain some expected elements
            if ("#root" in spring_el and ("&&" in spring_el or "?" in spring_el or "==" in spring_el)):
                passed += 1
                print(f"✅ {description}: PASSED")
            else:
                failed += 1
                print(f"❌ {description}: Unexpected output - {spring_el}")
                
        except Exception as e:
            failed += 1
            print(f"❌ {description}: ERROR - {str(e)}")
    
    print(f"\n📊 Immediate Fixes Summary:")
    print(f"✅ Whitespace handling tests passed: {passed}/{passed+failed}")
    print(f"📈 Success rate: {(passed/(passed+failed)*100):.1f}%" if (passed+failed) > 0 else "0%")
    
    # All our immediate fixes should be working
    assert passed == len(test_cases), f"Expected all {len(test_cases)} whitespace fixes to work, but only {passed} passed"
