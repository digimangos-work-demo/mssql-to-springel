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
            items = [str(item) for item in expr.right.value]
            return f"{{{', '.join(items)}}}.contains({left})"
        else:
            return f"{right}.contains({left})"

    # Special handling for NOT IN
    if expr.operator.upper() == 'NOT IN':
        if isinstance(expr.right, Literal) and expr.right.value_type == 'list':
            items = [str(item) for item in expr.right.value]
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

    return f"{context}.{expr.name}"


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
    
    # Parse WHEN...THEN pairs and ELSE clause
    when_clauses = []
    else_clause = None
    
    # Use a more careful approach to find WHEN clauses
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
        
        # Find the next WHEN or ELSE to determine where this THEN value ends
        rest_content = when_content[then_match.end():]
        
        # Look for next WHEN or ELSE
        next_when = re.search(r'\bWHEN\s+', rest_content, re.IGNORECASE)
        next_else = re.search(r'\bELSE\s+', rest_content, re.IGNORECASE)
        
        if next_else and (not next_when or next_else.start() < next_when.start()):
            # ELSE comes first or there's no more WHEN
            then_value = rest_content[:next_else.start()].strip()
            else_clause = rest_content[next_else.end():].strip()
            when_clauses.append((condition, then_value))
            break
        elif next_when:
            # Another WHEN comes next
            then_value = rest_content[:next_when.start()].strip()
            when_clauses.append((condition, then_value))
            remaining = rest_content[next_when.start():]
        else:
            # No more WHEN or ELSE, this is the last value
            then_value = rest_content.strip()
            when_clauses.append((condition, then_value))
            break
    
    if not when_clauses:
        return "'CASE_PARSE_ERROR'"
    
    # Convert to nested ternary operators
    result = else_clause if else_clause else 'null'
    
    # Build from right to left (last WHEN clause first)
    for condition, then_value in reversed(when_clauses):
        # Convert condition and value to Spring EL
        try:
            # Parse the condition as a simple expression
            from mylibrary.parser import _parse_simple_expression
            from mylibrary.converter import _convert_expression, _get_default_mappings
            
            condition_expr = _parse_simple_expression(condition)
            condition_el = _convert_expression(condition_expr, context, _get_default_mappings())
            
            # Handle quoted string literals in then_value
            if then_value.startswith("'") and then_value.endswith("'"):
                then_el = then_value  # Keep as-is for string literals
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
