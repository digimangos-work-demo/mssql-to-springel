"""
Test specifically for camelCase conversion improvements.
"""

import pytest
from mssql_to_spring_el.parser import parse_sql_logic
from mssql_to_spring_el.converter import to_spring_el


class TestCamelCaseConversion:
    """Tests specifically for camelCase conversion of hyphenated field names."""

    def test_simple_hyphenated_fields(self):
        """Test basic hyphenated field conversion to camelCase."""
        test_cases = [
            {
                'sql': 'WHERE [user-profile].[first-name] = "John"',
                'expected_contains': ['#root.userProfile.firstName'],
                'not_contains': ['user-profile', 'first-name']
            },
            {
                'sql': 'WHERE [employment-data].[salary-band] >= 75000',
                'expected_contains': ['#root.employmentData.salaryBand'],
                'not_contains': ['employment-data', 'salary-band']
            },
            {
                'sql': 'WHERE [performance-metrics].[rating] < 3.0',
                'expected_contains': ['#root.performanceMetrics.rating'],
                'not_contains': ['performance-metrics']
            }
        ]
        
        for case in test_cases:
            expression = parse_sql_logic(case['sql'])
            spring_el = to_spring_el(expression)
            
            for expected in case['expected_contains']:
                assert expected in spring_el, f"Expected '{expected}' in: {spring_el}"
            
            for forbidden in case['not_contains']:
                assert forbidden not in spring_el, f"Forbidden '{forbidden}' found in: {spring_el}"

    def test_complex_hyphenated_fields_in_expressions(self):
        """Test camelCase conversion in complex expressions."""
        sql = "WHERE [user-profile].[age-group] IN ('25-35', '36-45') AND [employment-data].[salary-band] >= 75000"
        expression = parse_sql_logic(sql)
        spring_el = to_spring_el(expression)
        
        # Should contain camelCase versions
        assert '#root.userProfile.ageGroup' in spring_el
        assert '#root.employmentData.salaryBand' in spring_el
        
        # Should NOT contain hyphenated versions
        assert 'user-profile' not in spring_el
        assert 'age-group' not in spring_el
        assert 'employment-data' not in spring_el
        assert 'salary-band' not in spring_el

    def test_ultimate_complexity_camelcase_conversion(self):
        """Test that camelCase conversion works in the ultimate complexity case."""
        sql = "CASE WHEN ([user-profile].[age-group] IN ('25-35', '36-45') AND [employment-data].[salary-band] >= 75000 AND NOT ([performance-metrics].[rating] < 3.0 OR [absence-records].[days-missed] > 15)) THEN CASE WHEN dept.[budget-allocation] > 500000 THEN 'High_Value_Employee' ELSE 'Standard_Employee' END WHEN contractor.[hourly-rate] BETWEEN 50 AND 150 AND proj.[deadline-pressure] = 'high' THEN 'Critical_Contractor' ELSE 'Regular_Worker' END AND ([audit-trail].[last-modified] >= '2023-06-01' OR [system-flags].[force-include] = true) AND NOT (usr.[email] LIKE '%@competitor.com' OR [security-clearance].[level] = 'restricted')"
        
        expression = parse_sql_logic(sql)
        spring_el = to_spring_el(expression)
        
        # All hyphenated field names should be converted to camelCase
        expected_camel_case = [
            'userProfile.ageGroup',
            'employmentData.salaryBand', 
            'performanceMetrics.rating',
            'absenceRecords.daysMissed',
            'dept.budgetAllocation',
            'auditTrail.lastModified',
            'systemFlags.forceInclude',
            'securityClearance.level'
        ]
        
        forbidden_hyphens = [
            'user-profile', 'age-group',
            'employment-data', 'salary-band',
            'performance-metrics', 'absence-records', 'days-missed',
            'budget-allocation', 'audit-trail', 'last-modified',
            'system-flags', 'force-include', 'security-clearance'
        ]
        
        for expected in expected_camel_case:
            assert expected in spring_el, f"Expected camelCase '{expected}' not found in: {spring_el}"
        
        for forbidden in forbidden_hyphens:
            assert forbidden not in spring_el, f"Forbidden hyphenated '{forbidden}' found in: {spring_el}"

    def test_mixed_case_and_underscore_preservation(self):
        """Test that underscores are preserved and case is maintained appropriately."""
        test_cases = [
            {
                'sql': 'WHERE [user_profile].[first_name] = "John"',
                'expected': '#root.user_profile.first_name',  # Underscores preserved
                'description': 'Underscores should be preserved'
            },
            {
                'sql': 'WHERE [UserProfile].[FirstName] = "John"',
                'expected': '#root.UserProfile.FirstName',  # Original case preserved
                'description': 'Original case should be preserved'
            },
            {
                'sql': 'WHERE [user-profile].[first_name] = "John"',
                'expected': '#root.userProfile.first_name',  # Hyphens converted, underscores preserved
                'description': 'Mixed hyphen and underscore handling'
            }
        ]
        
        for case in test_cases:
            expression = parse_sql_logic(case['sql'])
            spring_el = to_spring_el(expression)
            
            assert case['expected'] in spring_el, \
                f"{case['description']}: Expected '{case['expected']}' in: {spring_el}"