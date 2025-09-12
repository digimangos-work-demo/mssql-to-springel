"""
Converter from Expression objects to Spring EL strings.

This module traverses the expression AST and generates Spring EL syntax.
"""

import logging
from typing import Dict, Any
from mylibrary.logic_models import (
    Expression, BinaryOp, UnaryOp, FunctionCall,
    Literal, Variable, Conditional, LogicalGroup
)

# Configure logger
logger = logging.getLogger(__name__)


def to_spring_el(expression: Expression, context: str = "#root", mappings: Dict[str, str] = None) -> str:
    """
    Convert Expression object to Spring EL string.

    Args:
        expression: Parsed Expression object
        context: EL context prefix (default: "#root")
        mappings: Custom operator mappings (optional)

    Returns:
        Spring EL string representation

    Raises:
        ValueError: If expression is invalid
    """
    logger.debug(f"Converting expression to Spring EL: {expression}")
    logger.debug(f"Using context: {context}")
    
    if mappings is None:
        mappings = _get_default_mappings()

    result = _convert_expression(expression, context, mappings)
    logger.debug(f"Generated Spring EL: {result}")
    return result


def _get_default_mappings() -> Dict[str, str]:
    """Get default operator mappings."""
    return {
        'AND': '&&',
        'OR': '||',
        '=': '==',
        '!=': '!=',
        '<>': '!=',
        'NOT': '!',
        'IS': '==',
        'LIKE': 'matches',  # or =~ for regex
        'IN': 'contains'
    }


def _extract_then_value_with_nesting(content: str) -> tuple[str, str]:
    """
    Extract the THEN value from content, handling nested CASE statements.
    
    Returns:
        tuple: (then_value, remaining_content)
    """
    case_depth = 0
    i = 0
    
    while i < len(content):
        # Look for keywords
        remaining = content[i:].upper()
        
        if remaining.startswith('CASE '):
            case_depth += 1
            i += 5
        elif remaining.startswith('END') and (i + 3 >= len(content) or content[i + 3].isspace()):
            if case_depth > 0:
                case_depth -= 1
                i += 3
            else:
                # This END is not part of a nested CASE
                break
        elif case_depth == 0:
            # Only check for WHEN/ELSE when we're not inside a nested CASE
            if remaining.startswith('WHEN '):
                break
            elif remaining.startswith('ELSE '):
                break
        
        i += 1
    
    then_value = content[:i].strip()
    remaining_content = content[i:].strip()
    
    return then_value, remaining_content


def _convert_expression(expr: Expression, context: str, mappings: Dict[str, str]) -> str:
    """Convert expression to Spring EL."""
    if isinstance(expr, BinaryOp):
        return _convert_binary_op(expr, context, mappings)
    elif isinstance(expr, UnaryOp):
        return _convert_unary_op(expr, context, mappings)
    elif isinstance(expr, FunctionCall):
        return _convert_function_call(expr, context, mappings)
    elif isinstance(expr, Literal):
        return _convert_literal(expr)
    elif isinstance(expr, Variable):
        return _convert_variable(expr, context)
    elif isinstance(expr, Conditional):
        return _convert_conditional(expr, context, mappings)
    elif isinstance(expr, LogicalGroup):
        return f"({_convert_expression(expr.expression, context, mappings)})"
    else:
        raise ValueError(f"Unsupported expression type: {type(expr)}")


def _convert_binary_op(expr: BinaryOp, context: str, mappings: Dict[str, str]) -> str:
    """Convert binary operation."""
    left = _convert_expression(expr.left, context, mappings)
    right = _convert_expression(expr.right, context, mappings)
    op = mappings.get(expr.operator, expr.operator)

    # Special handling for LIKE
    if expr.operator.upper() == 'LIKE':
        # Convert SQL LIKE to Spring EL regex
        if isinstance(expr.right, Literal) and expr.right.value_type == 'string':
            pattern = expr.right.value.replace('%', '.*')
            return f"{left} =~ '{pattern}'"
        else:
            return f"{left} {op} {right}"

    # Special handling for IN
    if expr.operator.upper() == 'IN':
        if isinstance(expr.right, Literal) and expr.right.value_type == 'list':
            # Convert list items to properly quoted Spring EL set
            items = []
            for item in expr.right.value:
                if isinstance(item, str):
                    items.append(f"'{item}'")
                else:
                    items.append(str(item))
            return f"{{{', '.join(items)}}}.contains({left})"
        else:
            return f"{right}.contains({left})"

    # Special handling for NOT IN
    if expr.operator.upper() == 'NOT IN':
        if isinstance(expr.right, Literal) and expr.right.value_type == 'list':
            # Convert list items to properly quoted Spring EL set
            items = []
            for item in expr.right.value:
                if isinstance(item, str):
                    items.append(f"'{item}'")
                else:
                    items.append(str(item))
            return f"!{{{', '.join(items)}}}.contains({left})"
        else:
            return f"!{right}.contains({left})"

    # Add parentheses for compound conditions
    if expr.operator.upper() in ['AND', 'OR']:
        return f"({left}) {op} ({right})"

    return f"{left} {op} {right}"


def _convert_unary_op(expr: UnaryOp, context: str, mappings: Dict[str, str]) -> str:
    """Convert unary operation."""
    operand = _convert_expression(expr.operand, context, mappings)
    op = mappings.get(expr.operator, expr.operator)

    if expr.operator.upper() == 'NOT':
        # For NOT operations, wrap complex expressions in parentheses to ensure proper precedence
        if isinstance(expr.operand, BinaryOp) or '&&' in operand or '||' in operand or '==' in operand or '!=' in operand:
            return f"{op}({operand})"
        else:
            return f"{op}{operand}"
    elif expr.operator.upper() == 'IS NULL':
        return f"{operand} == null"
    elif expr.operator.upper() == 'IS NOT NULL':
        return f"{operand} != null"
    else:
        return f"{op} {operand}"


def _convert_function_call(expr: FunctionCall, context: str, mappings: Dict[str, str]) -> str:
    """Convert function call."""
    args = [_convert_expression(arg, context, mappings) for arg in expr.arguments]

    if expr.name.upper() == 'ISNULL':
        if len(args) == 2:
            return f"{args[0]} ?: {args[1]}"
        else:
            return f"{args[0]} ?: null"
    elif expr.name.upper() == 'COALESCE':
        return ' ?: '.join(args)
    else:
        # Generic function call
        arg_str = ', '.join(args)
        return f"{expr.name}({arg_str})"


def _convert_literal(expr: Literal) -> str:
    """Convert literal value."""
    if expr.value_type == 'string':
        return f"'{expr.value}'"
    elif expr.value_type == 'boolean':
        return str(expr.value).lower()
    elif expr.value_type == 'null':
        return 'null'
    else:
        return str(expr.value)


def _convert_variable(expr: Variable, context: str) -> str:
    """Convert variable/column."""
    # Special handling for CASE expressions stored as Variables
    if expr.name.upper().startswith('CASE ') and expr.name.upper().endswith(' END'):
        # Parse and convert CASE expression to Spring EL ternary operators
        return _convert_case_expression(expr.name, context)

    # Clean up bracket identifiers for Spring EL
    clean_name = _clean_identifier(expr.name)
    return f"{context}.{clean_name}"


def _clean_identifier(identifier: str) -> str:
    """
    Clean SQL identifiers for Spring EL property access.
    
    Removes brackets and converts hyphenated names to camelCase.
    Examples:
        [user_name] -> user_name
        [user-profile] -> userProfile
        [employment-data] -> employmentData
        u.[first-name] -> u.firstName
        [table].[column-name] -> table.columnName
    """
    # Remove square brackets
    cleaned = identifier.strip()
    
    # Handle cases like [table].[column] or u.[column]
    if '.' in cleaned:
        parts = cleaned.split('.')
        clean_parts = []
        for part in parts:
            # Remove brackets from each part
            clean_part = part.strip()
            if clean_part.startswith('[') and clean_part.endswith(']'):
                clean_part = clean_part[1:-1]
            # Convert hyphens to camelCase
            clean_part = _to_camel_case(clean_part)
            clean_parts.append(clean_part)
        return '.'.join(clean_parts)
    else:
        # Handle simple cases like [column]
        if cleaned.startswith('[') and cleaned.endswith(']'):
            cleaned = cleaned[1:-1]
        # Convert hyphens to camelCase
        cleaned = _to_camel_case(cleaned)
        return cleaned


def _to_camel_case(text: str) -> str:
    """
    Convert hyphenated text to camelCase.
    
    Examples:
        user-profile -> userProfile
        age-group -> ageGroup
        salary-band -> salaryBand
        first-name -> firstName
    """
    if '-' not in text:
        return text
    
    parts = text.split('-')
    # First part stays lowercase, subsequent parts are capitalized
    camel_case = parts[0].lower()
    for part in parts[1:]:
        if part:  # Handle double hyphens or trailing hyphens
            camel_case += part.capitalize()
    
    return camel_case


def _convert_conditional(expr: Conditional, context: str, mappings: Dict[str, str]) -> str:
    """Convert conditional (CASE) expression."""
    condition = _convert_expression(expr.condition, context, mappings)
    then_part = _convert_expression(expr.then_expr, context, mappings)
    else_part = _convert_expression(expr.else_expr, context, mappings)

    return f"{condition} ? {then_part} : {else_part}"


def _convert_case_expression(case_sql: str, context: str) -> str:
    """
    Convert a CASE SQL expression to Spring EL ternary operators.
    
    Converts: CASE WHEN condition1 THEN value1 WHEN condition2 THEN value2 ELSE value3 END
    To: condition1 ? value1 : (condition2 ? value2 : value3)
    """
    import re
    
    # Remove CASE and END keywords
    case_sql = case_sql.strip()
    if case_sql.upper().startswith('CASE '):
        case_sql = case_sql[5:].strip()
    if case_sql.upper().endswith(' END'):
        case_sql = case_sql[:-4].strip()
    
    # Parse WHEN...THEN pairs and ELSE clause with nested CASE support
    when_clauses = []
    else_clause = None
    
    # Use a more sophisticated parser that handles nested CASE statements
    remaining = case_sql
    
    while remaining:
        # Find the next WHEN
        when_match = re.search(r'\bWHEN\s+', remaining, re.IGNORECASE)
        if not when_match:
            break
            
        # Extract everything from WHEN onwards
        when_start = when_match.start()
        when_content = remaining[when_start + len(when_match.group()):]
        
        # Find the corresponding THEN
        then_match = re.search(r'\bTHEN\s+', when_content, re.IGNORECASE)
        if not then_match:
            break
            
        # Extract condition (between WHEN and THEN)
        condition = when_content[:then_match.start()].strip()
        
        # Find the next WHEN or ELSE, accounting for nested CASE statements
        rest_content = when_content[then_match.end():]
        
        # Parse the THEN value, which might contain nested CASE statements
        then_value, remaining_after_then = _extract_then_value_with_nesting(rest_content)
        
        when_clauses.append((condition, then_value))
        
        # Check if we found an ELSE clause
        if remaining_after_then.strip().upper().startswith('ELSE '):
            else_clause = remaining_after_then[5:].strip()
            break
        elif remaining_after_then.strip().upper().startswith('WHEN '):
            remaining = remaining_after_then
        else:
            break
    
    if not when_clauses:
        return "'CASE_PARSE_ERROR'"
    
    # Convert to nested ternary operators
    # Handle else clause - parse it like then values
    if else_clause:
        if else_clause.strip().upper().startswith('CASE '):
            # Recursively convert nested CASE statement
            result = _convert_case_expression(else_clause, context)
        elif else_clause.startswith("'") and else_clause.endswith("'"):
            result = else_clause  # Keep as-is for single-quoted strings
        elif else_clause.startswith('"') and else_clause.endswith('"'):
            # Convert double quotes to single quotes
            result = f"'{else_clause[1:-1]}'"
        else:
            # Try to parse as expression, fallback to literal
            try:
                from mylibrary.parser import _parse_simple_expression
                else_expr = _parse_simple_expression(else_clause)
                result = _convert_expression(else_expr, context, _get_default_mappings())
            except:
                result = f"'{else_clause}'"  # Treat as string literal
    else:
        result = 'null'
    
    # Build from right to left (last WHEN clause first)
    for condition, then_value in reversed(when_clauses):
        # Convert condition and value to Spring EL
        try:
            # Parse the condition as a simple expression
            from mylibrary.parser import _parse_simple_expression
            from mylibrary.converter import _convert_expression, _get_default_mappings
            
            condition_expr = _parse_simple_expression(condition)
            condition_el = _convert_expression(condition_expr, context, _get_default_mappings())
            
            # Handle then_value which might contain nested CASE statements
            if then_value.strip().upper().startswith('CASE '):
                # Recursively convert nested CASE statement
                then_el = _convert_case_expression(then_value, context)
            elif then_value.startswith("'") and then_value.endswith("'"):
                then_el = then_value  # Keep as-is for single-quoted strings
            elif then_value.startswith('"') and then_value.endswith('"'):
                # Convert double quotes to single quotes
                then_el = f"'{then_value[1:-1]}'"
            else:
                # Try to parse as expression, fallback to literal
                try:
                    then_expr = _parse_simple_expression(then_value)
                    then_el = _convert_expression(then_expr, context, _get_default_mappings())
                except:
                    then_el = f"'{then_value}'"  # Treat as string literal
            
            # Handle else clause similarly
            if result != 'null' and not result.startswith("'") and not result.startswith("("):
                if not any(op in result for op in ['?', '&&', '||', '==', '!=', '>', '<', '>=', '<=']):
                    result = f"'{result}'"
            
            result = f"({condition_el} ? {then_el} : {result})"
            
        except Exception as e:
            logger.warning(f"Failed to parse CASE condition '{condition}': {e}")
            # Fallback to simple text replacement for variables
            if ' ' not in condition and condition.isidentifier():
                condition_el = f"{context}.{condition}"
            else:
                condition_el = f"/* PARSE_ERROR: {condition} */ true"
            result = f"({condition_el} ? {then_value} : {result})"
    
    return result
