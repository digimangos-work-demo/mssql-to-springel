"""
Parser for MSSQL logical expressions.

This module parses MSSQL WHERE/HAVING clauses and CASE statements
into abstract syntax tree (AST) objects defined in logic_models.py.
"""

import re
import logging
from typing import Optional
from mylibrary.logic_models import (
    Expression, BinaryOp, UnaryOp, FunctionCall,
    Literal, Variable, Conditional, LogicalGroup
)

# Configure logger
logger = logging.getLogger(__name__)


def _is_numeric_literal(operand: str) -> bool:
    """
    Check if operand is a numeric literal (integer or decimal).
    
    Args:
        operand: The string to check
        
    Returns:
        True if operand represents a numeric literal, False otherwise
    """
    try:
        float(operand)
        return True
    except ValueError:
        return False


def _normalize_whitespace(sql: str) -> str:
    """
    Normalize whitespace in SQL while preserving string literals.
    
    This function:
    1. Preserves whitespace inside quoted strings
    2. Converts tabs to spaces
    3. Normalizes multiple whitespace to single spaces
    4. Handles newlines appropriately
    5. Ensures proper spacing around operators
    6. Handles minimal spacing cases (age>18AND -> age > 18 AND)
    """
    # Find all string literals (single and double quotes) first to protect them
    string_literals = []
    placeholder_pattern = "___STRING_LITERAL_{}___"
    
    # Extract string literals first before any processing
    def replace_string(match):
        string_literals.append(match.group(0))
        return placeholder_pattern.format(len(string_literals) - 1)
    
    # Replace strings with placeholders (both single and double quotes)
    sql_with_placeholders = re.sub(r"'[^']*'|\"[^\"]*\"", replace_string, sql)
    
    # Basic operator spacing will be handled later in the function
    # But handle string literal + operator cases that need immediate attention
    sql_with_placeholders = re.sub(r'(___STRING_LITERAL_\d+___)([A-Z]+)', r'\1 \2', sql_with_placeholders)
    sql_with_placeholders = re.sub(r'([A-Z]+)(___STRING_LITERAL_\d+___)', r'\1 \2', sql_with_placeholders)
    
    # Normalize whitespace in non-string portions
    # Convert tabs to spaces
    normalized = sql_with_placeholders.replace('\t', ' ')
    
    # Convert newlines to spaces
    normalized = normalized.replace('\n', ' ').replace('\r', ' ')
    
    # Add spaces around operators that might be missing them (minimal spacing fix)
    # Apply patterns multiple times to handle cascading fixes
    for _ in range(3):  # Multiple passes to handle complex cases
        operator_patterns = [
            # Comparison operators first
            (r'(\w)>=(\w)', r'\1 >= \2'),  # age>=18 -> age >= 18
            (r'(\w)<=(\w)', r'\1 <= \2'),  # age<=65 -> age <= 65  
            (r'(\w)!=(\w)', r'\1 != \2'),  # id!=0 -> id != 0
            (r'(\w)<>(\w)', r'\1 <> \2'),  # id<>0 -> id <> 0
            (r'(\w)=(\w)', r'\1 = \2'),    # status=active -> status = active (but be careful with strings)
            (r'(\w)>(\w)', r'\1 > \2'),    # age>18 -> age > 18
            (r'(\w)<(\w)', r'\1 < \2'),    # age<65 -> age < 65
            (r'(\w)IN\s*\(', r'\1 IN ('),  # statusIN( -> status IN (
            (r'(\w)NOT\s+IN\s*\(', r'\1 NOT IN ('),  # statusNOT IN( -> status NOT IN (
            # Handle numbers followed by AND/OR only when clearly separate tokens
            (r'(\d+)\s*AND\s*(\w)', r'\1 AND \2'),      # 18AND -> 18 AND  
            (r'(\d+)\s*OR\s*(\w)', r'\1 OR \2'),        # 18OR -> 18 OR
            (r'(\w)\s*AND\s*(\()', r'\1 AND \2'),       # status AND( -> status AND (
            (r'(\w)\s*OR\s*(\()', r'\1 OR \2'),         # status OR( -> status OR (
        ]
        
        for pattern, replacement in operator_patterns:
            normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
    
    # Collapse multiple spaces to single space
    normalized = re.sub(r'\s+', ' ', normalized)
    
    # Ensure proper spacing around key operators (be more selective)
    key_operators = [' AND ', ' OR ']
    for op in key_operators:
        # Ensure these critical operators have proper spacing
        pattern = op.strip()
        normalized = re.sub(rf'\s+{re.escape(pattern)}\s+', f' {pattern} ', normalized, flags=re.IGNORECASE)
    
    # Restore string literals
    for i, literal in enumerate(string_literals):
        normalized = normalized.replace(placeholder_pattern.format(i), literal)
    
    return normalized.strip()


def parse_sql_logic(sql_string: str) -> Expression:
    """
    Parse MSSQL logical expression into object model.

    Args:
        sql_string: MSSQL logic string (e.g., "WHERE age > 18 AND status = 'active'")

    Returns:
        Expression object representing the parsed logic

    Raises:
        ValueError: If SQL syntax is invalid or unsupported
        NotImplementedError: If feature is not yet implemented
    """
    if not sql_string or not sql_string.strip():
        logger.error("Empty SQL expression provided")
        raise ValueError("Empty SQL expression")

    logger.debug(f"Parsing SQL expression: {sql_string}")

    # NEW: Normalize whitespace first, before any processing
    sql_string = _normalize_whitespace(sql_string)
    logger.debug(f"Normalized whitespace: {sql_string}")

    # Remove WHERE/HAVING prefix if present
    sql_string = sql_string.strip()
    original_sql = sql_string
    if sql_string.upper().startswith('WHERE '):
        sql_string = sql_string[6:].strip()
        logger.debug(f"Removed WHERE prefix, parsing: {sql_string}")
    elif sql_string.upper().startswith('HAVING '):
        sql_string = sql_string[7:].strip()
        logger.debug(f"Removed HAVING prefix, parsing: {sql_string}")

    # Handle CASE expressions
    if sql_string.upper().startswith('CASE '):
        logger.debug("Detected CASE expression")
        return _parse_expression_with_case(sql_string)

    # Basic validation
    if not _is_valid_sql_expression(sql_string):
        logger.error(f"Invalid SQL expression: {sql_string}")
        raise ValueError(f"Invalid SQL expression: {sql_string}")

    # For now, implement a simple parser for basic expressions
    # This is a placeholder - full parsing would require a proper parser

    # Handle simple binary operations
    return _parse_simple_expression(sql_string)


def _parse_simple_expression(sql: str) -> Expression:
    """Parse simple expressions (placeholder implementation)."""
    sql = sql.strip()
    original_sql = sql  # Keep original for case preservation

    # Check for unsupported operators first
    unsupported_ops = [' MOD ', ' DIV ', ' % ', ' ^ ', ' & ', ' | ', ' << ', ' >> ']
    for op in unsupported_ops:
        if op in sql.upper():
            raise NotImplementedError(f"Operator '{op.strip()}' is not supported")

    # Handle parentheses - but only if they wrap the entire expression
    if sql.startswith('(') and sql.endswith(')'):
        # Check if these parentheses actually wrap the entire expression
        # by ensuring the closing paren matches the opening paren
        paren_count = 0
        for i, char in enumerate(sql):
            if char == '(':
                paren_count += 1
            elif char == ')':
                paren_count -= 1
                # If we reach 0 before the end, the parentheses don't wrap everything
                if paren_count == 0 and i < len(sql) - 1:
                    break
        
        # Only treat as wrapped expression if parentheses balance at the very end
        if paren_count == 0 and i == len(sql) - 1:
            inner = _parse_simple_expression(sql[1:-1])
            # If the inner expression is already a BinaryOp, don't wrap it in LogicalGroup
            if isinstance(inner, BinaryOp):
                return inner
            else:
                return LogicalGroup(inner)

    # Handle NOT operations
    if sql.upper().startswith('NOT '):
        operand = _parse_simple_expression(sql[4:].strip())
        return UnaryOp('NOT', operand)

    # Handle BETWEEN specially (before AND/OR to avoid splitting issues)
    # Support table-qualified identifiers in BETWEEN expressions
    between_match = re.match(r'^((?:\[?\w+(?:-\w+)*\]?\.)*\[?\w+(?:-\w+)*\]?)\s+BETWEEN\s+(.+?)\s+AND\s+(.+?)$', sql, re.IGNORECASE)
    if between_match:
        # Check if there are other operators besides the BETWEEN AND
        sql_upper = sql.upper()
        has_other_ops = False
        for op in [' AND ', ' OR ', ' NOT ', ' LIKE ', ' IN ', ' IS ']:
            if op in sql_upper:
                # If it's AND, check if it's part of BETWEEN ... AND ...
                if op == ' AND ':
                    # Count BETWEEN and AND
                    between_count = sql_upper.count('BETWEEN')
                    and_count = sql_upper.count(' AND ')
                    # If we have exactly one BETWEEN and one AND, it's okay
                    if not (between_count == 1 and and_count == 1):
                        has_other_ops = True
                        break
                else:
                    has_other_ops = True
                    break
        
        if not has_other_ops:
            left_part = between_match.group(1).strip()
            middle_part = between_match.group(2).strip()
            right_part = between_match.group(3).strip()
            left = _parse_operand(left_part)
            min_val = _parse_operand(middle_part)
            max_val = _parse_operand(right_part)
            
            # Create a compound expression: left >= min_val AND left <= max_val
            left_gte_min = BinaryOp(left, '>=', min_val)
            left_lte_max = BinaryOp(left, '<=', max_val)
            return BinaryOp(left_gte_min, 'AND', left_lte_max)

    # Handle AND/OR operations (simple split)
    and_parts = _split_by_operator(sql, ' AND ')
    if len(and_parts) > 1:
        left = _parse_simple_expression(and_parts[0])
        right = _parse_simple_expression(' AND '.join(and_parts[1:]))
        return BinaryOp(left, 'AND', right)

    or_parts = _split_by_operator(sql, ' OR ')
    if len(or_parts) > 1:
        left = _parse_simple_expression(or_parts[0])
        right = _parse_simple_expression(' OR '.join(or_parts[1:]))
        return BinaryOp(left, 'OR', right)

    # Handle function calls in operands  
    func_match = re.match(r'^(\w+)\s*\((.*)\)$', sql.strip(), re.DOTALL)
    if func_match:
        func_name = func_match.group(1)
        args_str = func_match.group(2).strip()
        if args_str:
            # Use proper comma parsing that respects quotes
            args = [_parse_operand(arg.strip()) for arg in _parse_comma_separated_list(args_str)]
        else:
            args = []
        return FunctionCall(func_name, args)
    
    # Handle NOT IN operator specially
    if ' NOT IN ' in sql.upper():
        parts = sql.upper().split(' NOT IN ')
        if len(parts) == 2:
            left_str = sql.split(' NOT IN ')[0].strip()
            right_str = sql.split(' NOT IN ')[1].strip()
            left = _parse_operand(left_str)
            
            # Special handling for NOT IN lists
            if right_str.startswith('(') and right_str.endswith(')'):
                # Parse NOT IN list
                list_content = right_str[1:-1].strip()
                if list_content:
                    items = _parse_comma_separated_list(list_content)
                    right = Literal(items, "list")
                else:
                    right = Literal([], "list")
            else:
                right = _parse_operand(right_str)
            
            return BinaryOp(left, 'NOT IN', right)

    comparison_ops = ['>=', '<=', '!=', '<>', '=', '>', '<', ' LIKE ', ' IN ', ' IS ']

    # Handle NOT LIKE specially
    if ' NOT LIKE ' in sql.upper():
        parts = sql.upper().split(' NOT LIKE ')
        if len(parts) == 2:
            left = _parse_operand(parts[0].strip())
            right_str = sql.split(' NOT LIKE ')[1].strip()
            right = _parse_operand(right_str)
            return BinaryOp(UnaryOp('NOT', left), 'LIKE', right)

    # Handle IS NULL and IS NOT NULL operators
    if ' IS NOT NULL' in sql.upper():
        parts = sql.upper().split(' IS NOT NULL')
        if len(parts) == 2 and parts[1].strip() == '':  # Ensure nothing after
            left_str = sql.split(' IS NOT NULL')[0].strip()
            left = _parse_operand(left_str)
            return UnaryOp('IS NOT NULL', left)
    
    if ' IS NULL' in sql.upper():
        parts = sql.upper().split(' IS NULL')
        if len(parts) == 2 and parts[1].strip() == '':  # Ensure nothing after
            left_str = sql.split(' IS NULL')[0].strip()
            left = _parse_operand(left_str)
            return UnaryOp('IS NULL', left)

    # Handle comparisons
    comparison_ops = ['>=', '<=', '!=', '<>', '=', '>', '<', ' LIKE ', ' IN ', ' IS ']
    for op in comparison_ops:
        if op in sql.upper():
            # Split on the operator with proper case handling
            # For spaced operators like ' IN ', split on the original spaces to avoid false matches
            if op.startswith(' ') and op.endswith(' '):
                # Find the operator in the original SQL (preserving case)
                op_upper = op.upper()
                sql_upper = sql.upper()
                op_pos = sql_upper.find(op_upper)
                if op_pos != -1:
                    left_part = sql[:op_pos]
                    right_part = sql[op_pos + len(op):]
                    parts = [left_part, right_part]
                else:
                    continue
            else:
                parts = sql.split(op.strip())  # For non-spaced operators
                
            if len(parts) == 2:
                left = _parse_operand(parts[0].strip())
                right_str = parts[1].strip()

                # Special handling for IN lists
                if op.strip().upper() == 'IN':
                    if right_str.startswith('(') and right_str.endswith(')'):
                        # Parse IN list
                        list_content = right_str[1:-1].strip()
                        if list_content:
                            items = _parse_comma_separated_list(list_content)
                            right = Literal(items, "list")
                        else:
                            right = Literal([], "list")
                    else:
                        right = _parse_operand(right_str)
                else:
                    right = _parse_operand(right_str)

                return BinaryOp(left, op.strip(), right)

    # Handle single operands
    return _parse_operand(sql)


def _parse_comma_separated_list(content: str) -> list:
    """Parse a comma-separated list respecting quotes."""
    items = []
    current = ""
    in_string = False
    string_char = None
    
    i = 0
    while i < len(content):
        char = content[i]
        
        if char in ["'", '"'] and not in_string:
            # Start of quoted string
            in_string = True
            string_char = char
            current += char
        elif char == string_char and in_string:
            # End of quoted string
            in_string = False
            string_char = None
            current += char
        elif in_string:
            # Inside quoted string
            current += char
        elif char == ',' and not in_string:
            # Comma outside quotes - end of item
            if current.strip():
                items.append(current.strip().strip("'\""))
            current = ""
        else:
            current += char
        i += 1
    
    # Add final item
    if current.strip():
        items.append(current.strip().strip("'\""))
    
    return items


def _split_by_operator(sql: str, operator: str) -> list:
    """Split SQL by operator, respecting parentheses, string literals, and BETWEEN expressions."""
    parts = []
    current = ""
    paren_depth = 0
    in_between = False
    in_string = False
    string_char = None

    i = 0
    while i < len(sql):
        char = sql[i]
        
        # Handle string literals - don't split inside quotes
        if char in ["'", '"'] and not in_string:
            in_string = True
            string_char = char
            current += char
        elif char == string_char and in_string:
            in_string = False
            string_char = None
            current += char
        elif in_string:
            # Inside string literal - just add character
            current += char
        elif char == '(':
            paren_depth += 1
            current += char
        elif char == ')':
            paren_depth -= 1
            current += char
        elif paren_depth == 0:
            # Check for BETWEEN start
            if sql[i:i+7].upper() == 'BETWEEN':
                in_between = True
                current += sql[i:i+7]  # Add "BETWEEN"
                i += 6  # Skip ahead, will be incremented at end
            # Check for AND after BETWEEN
            elif in_between and sql[i:i+4].upper() == ' AND':
                # This is the AND in BETWEEN ... AND ..., don't split here
                current += sql[i:i+4]  # Add " AND"
                i += 3  # Skip ahead, will be incremented at end
                in_between = False  # Reset flag
            elif not in_between and sql[i:i+len(operator)].upper() == operator.upper():
                parts.append(current.strip())
                current = ""
                i += len(operator) - 1  # Skip operator, will be incremented at end
            else:
                current += char
        else:
            current += char
        i += 1

    if current.strip():
        parts.append(current.strip())

    return parts


def _parse_operand(operand: str) -> Expression:
    """Parse a single operand."""
    operand = operand.strip()

    # Handle function calls - make regex more flexible
    func_match = re.match(r'^(\w+)\s*\((.*)\)$', operand, re.DOTALL)
    if func_match:
        func_name = func_match.group(1)
        args_str = func_match.group(2).strip()
        if args_str:
            # Simple argument parsing - split by comma, but this is basic
            args = [_parse_operand(arg.strip()) for arg in args_str.split(',')]
        else:
            args = []
        return FunctionCall(func_name, args)

    # Handle parenthetical expressions
    if operand.startswith('(') and operand.endswith(')'):
        # Parse the content inside parentheses as a full expression
        inner_sql = operand[1:-1].strip()
        return _parse_simple_expression(inner_sql)

    # Handle literals
    if operand.startswith("'") and operand.endswith("'"):
        return Literal(operand[1:-1], "string")
    elif operand.startswith('"') and operand.endswith('"'):
        return Literal(operand[1:-1], "string")  # Handle double quotes too
    elif operand.isdigit():
        return Literal(int(operand), "number")
    elif _is_numeric_literal(operand):
        # Handle decimal numbers like 3.0, 85.5, 2.1, etc.
        return Literal(float(operand), "number")
    elif operand.lower() in ['true', 'false']:
        return Literal(operand.lower() == 'true', "boolean")
    elif operand.upper() == 'NULL':
        return Literal(None, "null")

    # Handle variables/columns - including table-qualified identifiers
    else:
        # Check for table-qualified identifiers: table.column or [table].[column]
        if '.' in operand:
            return _parse_qualified_identifier(operand)
        
        # Check for square bracket identifiers: [column-name]
        if operand.startswith('[') and operand.endswith(']'):
            # Extract the identifier from brackets
            identifier = operand[1:-1]
            return Variable(f"[{identifier}]")  # Keep brackets to indicate special identifier
        
        # Regular identifier validation (letters, numbers, underscores, no spaces)
        if not operand.replace('_', '').isalnum() or ' ' in operand:
            raise ValueError(f"Invalid operand: {operand}")
        return Variable(operand)


def _parse_qualified_identifier(operand: str) -> Expression:
    """
    Parse table-qualified identifiers like table.column or [table].[column].
    
    Supports:
    - table.column (simple case)
    - [table].[column] (square brackets)
    - [table-with-special].[column-chars]
    - alias.[column-name]
    """
    # Split on the dot
    if '.' not in operand:
        raise ValueError(f"Expected qualified identifier with dot: {operand}")
    
    parts = operand.split('.', 1)  # Split on first dot only
    if len(parts) != 2:
        raise ValueError(f"Invalid qualified identifier format: {operand}")
    
    table_part = parts[0].strip()
    column_part = parts[1].strip()
    
    # Clean up square brackets if present
    if table_part.startswith('[') and table_part.endswith(']'):
        table_name = table_part[1:-1]
        table_bracket_style = True
    else:
        table_name = table_part
        table_bracket_style = False
    
    if column_part.startswith('[') and column_part.endswith(']'):
        column_name = column_part[1:-1]
        column_bracket_style = True
    else:
        column_name = column_part
        column_bracket_style = False
    
    # For now, create a variable with the qualified name
    # Later we can create a specialized QualifiedVariable class
    if table_bracket_style or column_bracket_style:
        # Use bracket notation to preserve special characters
        qualified_name = f"[{table_name}].[{column_name}]"
    else:
        # Simple dot notation
        qualified_name = f"{table_name}.{column_name}"
    
    return Variable(qualified_name)


def _is_valid_sql_expression(sql: str) -> bool:
    """Basic validation for SQL expressions."""
    sql = sql.strip()

    # Check for obviously invalid patterns
    if sql.upper().startswith(('SELECT ', 'INSERT ', 'UPDATE ', 'DELETE ', 'CREATE ', 'DROP ')):
        return False

    # Check for unmatched parentheses
    paren_count = 0
    for char in sql:
        if char == '(':
            paren_count += 1
        elif char == ')':
            paren_count -= 1
            if paren_count < 0:
                return False

    if paren_count != 0:
        return False

    # Check for basic structure - should have some operators or be a simple expression
    if not any(op in sql.upper() for op in ['AND', 'OR', 'NOT', '>', '<', '=', 'LIKE', 'IN', 'IS', 'CASE']):
        # If no operators, should be a simple variable or literal
        if not sql.replace(' ', '').replace("'", '').replace('"', '').isalnum():
            return False

    return True


def _parse_case_expression(sql: str) -> Expression:
    """Parse CASE expression into Conditional."""
    # For now, return a placeholder - full CASE parsing is complex
    # This is a simplified implementation for basic cases

    sql = sql.strip()
    if not sql.upper().endswith(' END'):
        raise ValueError("CASE expression must end with 'END'")

    # Simple approach: just return the original SQL as a Variable for now
    # This allows the converter to handle it
    return Variable(sql)


def _parse_expression_with_case(sql: str) -> Expression:
    """Parse expression that starts with CASE and may have additional operators."""
    sql = sql.strip()
    sql_upper = sql.upper()
    
    # Find the matching END for the CASE expression
    case_end_pos = _find_case_end_position(sql)
    
    if case_end_pos == -1:
        raise ValueError("CASE expression must have matching END")
    
    # Extract the CASE expression
    case_expr = sql[:case_end_pos + 3]  # +3 for "END"
    
    # Check if there's more after the END
    remaining = sql[case_end_pos + 3:].strip()
    
    if not remaining:
        # Just a CASE expression
        return _parse_case_expression(case_expr)
    
    # There's more after the CASE expression, need to parse as binary operation
    case_operand = _parse_case_expression(case_expr)
    
    # Parse the remaining part as a continuation
    # Look for logical operators (AND, OR) at the beginning of remaining
    remaining_upper = remaining.upper()
    if remaining_upper.startswith('AND '):
        right_operand = _parse_simple_expression(remaining[4:].strip())
        return BinaryOp(case_operand, 'AND', right_operand)
    elif remaining_upper.startswith('OR '):
        right_operand = _parse_simple_expression(remaining[3:].strip())
        return BinaryOp(case_operand, 'OR', right_operand)
    else:
        # If no logical operator, assume AND (this might need adjustment)
        raise ValueError(f"Expected logical operator after CASE expression, found: {remaining}")


def _find_case_end_position(sql: str) -> int:
    """Find the position of the END keyword that closes the CASE expression."""
    sql_upper = sql.upper()
    
    # Simple approach: count CASE and END keywords
    # This assumes no nested CASE expressions for now
    case_count = 0
    end_count = 0
    i = 0
    
    while i < len(sql):
        if sql_upper[i:].startswith('CASE '):
            case_count += 1
            i += 5  # Skip "CASE "
        elif sql_upper[i:].startswith(' END') and (i + 4 >= len(sql) or not sql[i + 4].isalnum()):
            end_count += 1
            if case_count == end_count:
                return i + 1  # Return position of 'E' in "END"
            i += 4  # Skip " END"
        elif sql_upper[i:].startswith('END ') or (sql_upper[i:].startswith('END') and i + 3 >= len(sql)):
            end_count += 1
            if case_count == end_count:
                return i  # Return position of 'E' in "END"
            i += 3  # Skip "END"
        else:
            i += 1
    
    return -1  # No matching END found
