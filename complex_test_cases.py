#!/usr/bin/env python3
"""
Complex SQL test cases for the MSSQL to Spring EL converter.
These demonstrate various levels of complexi        # Level 20: The ultimate nightmare scenario
        {
            "name": "Ultimate nightmare complexity",
            "sql": "CASE WHEN ([user-profile].[age-group] IN ('25-35', '36-45') AND [employment-data].[salary-band] >= 75000 AND NOT ([performance-metrics].[rating] < 3.0 OR [absence-records].[days-missed] > 15)) THEN CASE WHEN dept.[budget-allocation] > 500000 THEN 'High_Value_Employee' ELSE 'Standard_Employee' END WHEN contractor.[hourly-rate] BETWEEN 50 AND 150 AND proj.[deadline-pressure] = 'high' THEN 'Critical_Contractor' ELSE 'Regular_Worker' END AND ([audit-trail].[last-modified] >= '2023-06-01' OR [system-flags].[force-include] = true) AND NOT (usr.[email] LIKE '%@competitor.com' OR [security-clearance].[level] = 'restricted')",
        },
        
        # Whitespace Edge Cases
        {
            "name": "Extra spaces everywhere",
            "sql": "WHERE   age    >    18   AND    status   =   'active'   OR    department    IN    ('IT',   'HR')  ",
        },
        
        {
            "name": "Tabs instead of spaces",
            "sql": "WHERE\tage\t>\t18\tAND\tstatus\t=\t'active'\tOR\tdepartment\tIN\t('IT',\t'HR')",
        },
        
        {
            "name": "Multiline SQL with mixed whitespace",
            "sql": "WHERE age > 18\n            AND status = 'active'\n            OR (department IN ('IT', 'HR')\n                AND salary >= 50000)",
        },
        
        {
            "name": "Chaotic whitespace mix",
            "sql": "WHERE  \\t age\\t> \\n18   AND\\t\\t\\n            status =  'active' \\t\\n            OR   \\tdepartment\\nIN  ('IT',\\t'HR')",
        },
        
        {
            "name": "CASE with newlines and tabs",
            "sql": "CASE\\tWHEN age\\n>\\t65\\n            THEN\\t'Senior'\\n            WHEN\\nage > 18\\t\\n            THEN 'Adult'\\n\\n            ELSE   'Minor'\\t\\n            END",
        },
        
        {
            "name": "Functions with whitespace chaos",
            "sql": "WHERE ISNULL\\t(\\n  name  ,\\t  'Unknown'\\n  )\\t=  'John'\\tAND\\nLEN( description\\t) >  100",
        },
        
        {
            "name": "Whitespace in string literals preserved",
            "sql": "WHERE description = 'This has  multiple   spaces' AND comment = '  Leading and trailing  '",
        },
        
        {
            "name": "Minimal spacing (challenging)",
            "sql": "WHERE age>18AND status='active'OR department='IT'",
        },d edge cases.

This file can be run standalone to see what works and what doesn't,
helping identify areas for improvement in the parser.
"""

import sys
import json
from mylibrary.parser import parse_sql_logic
from mylibrary.converter import to_spring_el

def test_complex_cases():
    """Test increasingly complex SQL expressions."""
    
    test_cases = [
        # Level 1: Basic CASE with additional conditions
        {
            "name": "Basic CASE with AND",
            "sql": "CASE WHEN age > 65 THEN 'Senior' WHEN age > 18 THEN 'Adult' ELSE 'Minor' END AND status = 'active'",
        },
        
        # Level 2: Multiple logical operators
        {
            "name": "Complex logical combinations",
            "sql": "WHERE (age >= 18 AND age <= 65) AND (status IN ('active', 'pending', 'verified') OR is_premium = true) AND NOT (name LIKE 'Test%')",
        },
        
        # Level 3: Nested parentheses and functions
        {
            "name": "Nested conditions with functions",
            "sql": "WHERE (ISNULL(first_name, '') != '' AND ISNULL(last_name, '') != '') AND ((age BETWEEN 25 AND 55) OR (experience_years >= 10))",
        },
        
        # Level 4: Complex CASE with simple conditions
        {
            "name": "Multi-branch CASE",
            "sql": "CASE WHEN score >= 90 THEN 'A' WHEN score >= 80 THEN 'B' WHEN score >= 70 THEN 'C' WHEN score >= 60 THEN 'D' ELSE 'F' END",
        },
        
        # Level 5: CASE with additional complex logic
        {
            "name": "CASE with complex follow-up",
            "sql": "CASE WHEN priority = 1 THEN 'High' WHEN priority = 2 THEN 'Medium' ELSE 'Low' END AND assigned_to IS NOT NULL AND due_date >= '2023-01-01'",
        },
        
        # Level 6: Multiple IN clauses and ranges
        {
            "name": "Multiple IN and BETWEEN",
            "sql": "WHERE department IN ('Sales', 'Marketing', 'Support') AND salary BETWEEN 40000 AND 120000 AND location IN ('NYC', 'SF', 'LA', 'Chicago')",
        },
        
        # Level 7: Complex nested logical structure
        {
            "name": "Deep logical nesting",
            "sql": "WHERE ((type = 'employee' AND (role IN ('manager', 'director') OR seniority_level >= 5)) OR (type = 'contractor' AND hourly_rate >= 75)) AND status = 'active'",
        },
        
        # Level 8: Functions with CASE
        {
            "name": "Functions with CASE result",
            "sql": "CASE WHEN LEN(description) > 100 THEN 'Long' WHEN LEN(description) > 50 THEN 'Medium' ELSE 'Short' END AND category != 'archived'",
        },
        
        # Level 9: Multiple comparisons with different operators
        {
            "name": "Mixed comparison operators",
            "sql": "WHERE created_date >= '2023-01-01' AND modified_date <= '2023-12-31' AND version_number > 1.0 AND status != 'deleted' AND owner_id <> 0",
        },
        
        # Level 10: Table aliases and square brackets
        {
            "name": "Table aliases with square brackets",
            "sql": "WHERE u.[first_name] IS NOT NULL AND p.[project_name] LIKE 'Critical%' AND d.[department_code] IN ('IT', 'HR') AND e.[employee_id] = u.[user_id]",
        },
        
        # Level 11: Mixed aliases and complex conditions
        {
            "name": "Mixed table aliases",
            "sql": "WHERE (emp.[salary] BETWEEN 50000 AND 150000 AND dept.[budget] > 1000000) OR (contractor.hourly_rate >= 75 AND proj.[priority_level] = 1)",
        },
        
        # Level 12: Square brackets with special characters
        {
            "name": "Special characters in brackets",
            "sql": "WHERE [user-data].[email-address] LIKE '%@company.com' AND [sys info].[last login] >= '2023-01-01' AND [config].[feature-flags] = 'enabled'",
        },
        
        # Level 13: Complex CASE with table aliases
        {
            "name": "CASE with table aliases and brackets",
            "sql": "CASE WHEN emp.[department_id] = dept.[id] AND dept.[name] = 'Engineering' THEN emp.[base_salary] * 1.15 WHEN emp.[years_experience] >= 10 THEN emp.[base_salary] * 1.10 ELSE emp.[base_salary] END",
        },
        
        # Level 14: Nested functions with aliases
        {
            "name": "Functions with table aliases",
            "sql": "WHERE ISNULL(u.[middle_name], '') != '' AND LEN(p.[description]) > 100 AND UPPER(d.[department_name]) IN ('SALES', 'MARKETING')",
        },
        
        # Level 15: Multiple table complex joins logic
        {
            "name": "Multi-table complex logic",
            "sql": "WHERE (users.id = profiles.[user_id] AND profiles.[is_verified] = true) AND (orders.[total_amount] >= 500 OR customers.[loyalty_tier] IN ('Gold', 'Platinum')) AND NOT (users.[email] LIKE '%test%' OR users.[status] = 'suspended')",
        },
        
        # Level 16: Reserved word conflicts
        {
            "name": "Reserved words in brackets",
            "sql": "WHERE [order].[date] >= '2023-01-01' AND [user].[group] IN ('admin', 'manager') AND [select].[value] IS NOT NULL AND [table].[index] > 0",
        },
        
        # Level 17: Numbers and special characters in identifiers
        {
            "name": "Numbers and special chars",
            "sql": "WHERE tbl1.[field_1] = 'value' AND [table-2].[column@3] LIKE 'prefix%' AND alias3.[field$4] BETWEEN 1.5 AND 9.8",
        },
        
        # Level 18: Deep nesting with aliases
        {
            "name": "Deep nested conditions with aliases",
            "sql": "WHERE ((emp.[department] = 'IT' AND (proj.[status] = 'active' OR proj.[priority] >= 3)) AND (mgr.[approval_date] IS NOT NULL OR exec.[override] = true)) OR (contractor.[rate] >= 100 AND vendor.[rating] >= 4.5)",
        },
        
        # Level 19: CASE with complex alias conditions
        {
            "name": "Complex CASE with multiple aliases",
            "sql": "CASE WHEN emp.[years_service] >= 20 AND dept.[type] = 'core' THEN 'Senior_Core' WHEN emp.[performance_rating] >= 4.5 AND proj.[complexity] = 'high' THEN 'High_Performer' WHEN mgr.[recommendation] = 'promote' THEN 'Promotion_Ready' ELSE 'Standard' END AND emp.[is_active] = true",
        },
        
        # Level 20: The ultimate nightmare scenario
        {
            "name": "Ultimate nightmare complexity",
            "sql": "CASE WHEN ([user-profile].[age-group] IN ('25-35', '36-45') AND [employment-data].[salary-band] >= 75000 AND NOT ([performance-metrics].[rating] < 3.0 OR [absence-records].[days-missed] > 15)) THEN CASE WHEN dept.[budget-allocation] > 500000 THEN 'High_Value_Employee' ELSE 'Standard_Employee' END WHEN contractor.[hourly-rate] BETWEEN 50 AND 150 AND proj.[deadline-pressure] = 'high' THEN 'Critical_Contractor' ELSE 'Regular_Worker' END AND ([audit-trail].[last-modified] >= '2023-06-01' OR [system-flags].[force-include] = true) AND NOT (usr.[email] LIKE '%@competitor.com' OR [security-clearance].[level] = 'restricted')",
        }
    ]
    
    print("🧪 Testing Complex SQL Expressions")
    print("This helps identify current parser capabilities and limitations\n")
    print("=" * 80)
    
    passed = 0
    failed = 0
    skipped = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test {i}: {test_case['name']}")
        print("-" * 60)
        print(f"SQL: {test_case['sql']}")
        
        try:
            # Parse the expression
            expression = parse_sql_logic(test_case['sql'])
            print(f"✅ Parsed successfully: {type(expression).__name__}")
            
            # Convert to Spring EL
            spring_el = to_spring_el(expression)
            print(f"🔄 Spring EL: {spring_el}")
            
            # Check for parse errors or limitations
            if "PARSE_ERROR" in spring_el:
                print("⚠️  Contains parse errors - partial functionality")
                skipped += 1
            else:
                print("✅ Fully converted")
                passed += 1
            
            # Test JSON output (optional, only show for first few)
            if i <= 3:
                expr_dict = expression.to_dict()
                print(f"📄 JSON: {json.dumps(expr_dict, indent=2)}")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            failed += 1
        
        print("\n" + "=" * 80)
    
    # Summary
    print(f"\n📊 Summary:")
    print(f"✅ Fully working: {passed}")
    print(f"⚠️  Partial/Limited: {skipped}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success rate: {(passed/(passed+failed+skipped)*100):.1f}%" if (passed+failed+skipped) > 0 else "0%")
    
    return passed, skipped, failed

def run_specific_test(test_name_pattern=None):
    """Run a specific test or pattern."""
    if not test_name_pattern:
        return test_complex_cases()
    
    # You could add filtering logic here
    return test_complex_cases()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        pattern = sys.argv[1]
        run_specific_test(pattern)
    else:
        test_complex_cases()
