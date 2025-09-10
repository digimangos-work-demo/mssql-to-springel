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

    # Handle parentheses
    if sql.startswith('(') and sql.endswith(')'):
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
    # Only match BETWEEN when it's a simple variable BETWEEN value AND value
    # Make sure it's not part of a larger expression by checking for operators
    between_match = re.match(r'^(\w+(?:\.\w+)*)\s+BETWEEN\s+(.+?)\s+AND\s+(.+?)$', sql, re.IGNORECASE)
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
            middle = _parse_operand(middle_part)
            right = _parse_operand(right_part)
            return FunctionCall('BETWEEN', [left, middle, right])

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
    func_match = re.match(r'^(\w+)\s*\((.*)\)$', sql.strip())
    if func_match:
        func_name = func_match.group(1)
        args_str = func_match.group(2).strip()
        if args_str:
            # Simple argument parsing - split by comma, but this is basic
            args = [_parse_operand(arg.strip()) for arg in args_str.split(',')]
        else:
            args = []
        return FunctionCall(func_name, args)
    comparison_ops = ['>=', '<=', '!=', '<>', '=', '>', '<', ' LIKE ', ' IN ', ' IS ']

    # Handle NOT LIKE specially
    if ' NOT LIKE ' in sql.upper():
        parts = sql.upper().split(' NOT LIKE ')
        if len(parts) == 2:
            left = _parse_operand(parts[0].strip())
            right_str = sql.split(' NOT LIKE ')[1].strip()
            right = _parse_operand(right_str)
            return BinaryOp(UnaryOp('NOT', left), 'LIKE', right)

    # Handle comparisons
    comparison_ops = ['>=', '<=', '!=', '<>', '=', '>', '<', ' LIKE ', ' IN ', ' IS ']
    for op in comparison_ops:
        if op in sql.upper():
            parts = sql.split(op.strip())  # Split on original case
            if len(parts) == 2:
                left = _parse_operand(parts[0].strip())
                right_str = parts[1].strip()

                # Special handling for IN lists
                if op.strip().upper() == 'IN':
                    if right_str.startswith('(') and right_str.endswith(')'):
                        # Parse IN list
                        list_content = right_str[1:-1].strip()
                        if list_content:
                            items = [item.strip().strip("'\"") for item in list_content.split(',')]
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


def _split_by_operator(sql: str, operator: str) -> list:
    """Split SQL by operator, respecting parentheses and BETWEEN expressions."""
    parts = []
    current = ""
    paren_depth = 0
    in_between = False

    i = 0
    while i < len(sql):
        char = sql[i]
        if char == '(':
            paren_depth += 1
            current += char
        elif char == ')':
            paren_depth -= 1
            current += char
        elif paren_depth == 0:
            # Check for BETWEEN start
            if sql[i:i+7].upper() == 'BETWEEN':
                in_between = True
                current += char
            # Check for AND after BETWEEN
            elif in_between and sql[i:i+3].upper() == 'AND':
                # This is the AND in BETWEEN ... AND ..., don't split here
                current += char
                if sql[i:i+7].upper() == 'AND ':
                    i += 3  # Skip the "AND" but keep the space
                    continue
            elif not in_between and sql[i:i+len(operator)].upper() == operator.upper():
                parts.append(current)
                current = ""
                i += len(operator)
                continue
            else:
                current += char
        else:
            current += char
        i += 1

    if current:
        parts.append(current)

    return parts


def _parse_operand(operand: str) -> Expression:
    """Parse a single operand."""
    operand = operand.strip()

    # Handle function calls
    func_match = re.match(r'^(\w+)\s*\((.*)\)$', operand)
    if func_match:
        func_name = func_match.group(1)
        args_str = func_match.group(2).strip()
        if args_str:
            # Simple argument parsing - split by comma, but this is basic
            args = [_parse_operand(arg.strip()) for arg in args_str.split(',')]
        else:
            args = []
        return FunctionCall(func_name, args)

    # Handle literals
    if operand.startswith("'") and operand.endswith("'"):
        return Literal(operand[1:-1], "string")
    elif operand.isdigit():
        return Literal(int(operand), "number")
    elif operand.lower() in ['true', 'false']:
        return Literal(operand.lower() == 'true', "boolean")
    elif operand.upper() == 'NULL':
        return Literal(None, "null")

    # Handle variables/columns - must be valid identifiers
    else:
        # Check if it's a valid identifier (letters, numbers, underscores, no spaces)
        if not operand.replace('_', '').replace('.', '').isalnum() or ' ' in operand:
            raise ValueError(f"Invalid operand: {operand}")
        return Variable(operand)


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
