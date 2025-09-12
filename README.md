# MSSQL Logic Parser to Spring EL Converter

A Python library that parses Microsoft SQL Server (MSSQL) WHERE clauses, HAVING clauses, and CASE expressions, then converts them to Spring Expression Language (SpEL) format.

## Features

- **Parse MSSQL Logic**: Convert SQL logical expressions into Abstract Syntax Tree (AST) objects
- **Spring EL Output**: Generate Spring Expression Language strings for use in Spring frameworks
- **Command Line Interface**: Easy-to-use CLI for quick conversions
- **Multiple Formats**: Support for JSON and text output formats
- **Custom Context**: Configurable Spring EL context prefixes
- **Comprehensive Support**: Handles comparisons, logical operators, functions, CASE expressions, and more

## Installation

```bash
pip install .
```

## Quick Start

### Command Line Usage

```bash
# Basic conversion
python -m mssql_to_spring_el "WHERE age > 18 AND name LIKE 'John%'"

# JSON output format
python -m mssql_to_spring_el --format json "WHERE status = 'active'"

# Custom Spring EL context
python -m mssql_to_spring_el --context "#user" "WHERE role = 'admin'"

# Show version
python -m mssql_to_spring_el --version

# Show help
python -m mssql_to_spring_el --help
```

### Python API Usage

```python
from mssql_to_spring_el.parser import parse_sql_logic
from mssql_to_spring_el.converter import to_spring_el

# Parse MSSQL logic
sql = "WHERE age BETWEEN 18 AND 65 AND status = 'active'"
expression = parse_sql_logic(sql)

# Convert to Spring EL
spring_el = to_spring_el(expression)
print(spring_el)  # Output: (#root.age >= 18 and #root.age <= 65) and #root.status == 'active'

# Custom context and mappings
spring_el = to_spring_el(expression, context="#user", mappings={"=": " eq "})
print(spring_el)  # Output: (#user.age >= 18 and #user.age <= 65) and #user.status eq 'active'
```

## Supported SQL Features

### Comparison Operators
- `=`, `!=`, `<>`, `<`, `<=`, `>`, `>=`
- `LIKE` patterns with wildcards
- `IN` lists: `column IN (value1, value2, value3)`
- `IS NULL` and `IS NOT NULL`
- `BETWEEN` ranges: `column BETWEEN min AND max`

### Logical Operators
- `AND`, `OR`, `NOT`
- Parentheses for grouping: `(condition1 OR condition2) AND condition3`

### Functions
- Built-in functions: `ISNULL(column, default)`, `LEN(column)`, etc.
- Custom function support

### CASE Expressions
- Simple CASE statements
- Complex conditional logic

### Data Types
- Strings (single quotes): `'John Doe'`
- Numbers: `42`, `3.14`
- Booleans: `TRUE`, `FALSE`
- NULL values

## API Reference

### Core Functions

#### `parse_sql_logic(sql_string: str) -> Expression`

Parses MSSQL logical expressions into AST objects.

**Parameters:**
- `sql_string`: SQL WHERE/HAVING clause or CASE expression

**Returns:**
- `Expression`: Parsed AST object

**Raises:**
- `ValueError`: Invalid SQL syntax
- `NotImplementedError`: Unsupported features

**Example:**
```python
from mssql_to_spring_el.parser import parse_sql_logic

# Simple comparison
expr = parse_sql_logic("WHERE age > 18")

# Complex expression
expr = parse_sql_logic("WHERE (name LIKE 'J%' OR email IS NOT NULL) AND status IN ('active', 'pending')")
```

#### `to_spring_el(expression: Expression, context: str = "#root", mappings: Dict[str, str] = None) -> str`

Converts Expression objects to Spring EL strings.

**Parameters:**
- `expression`: Parsed Expression object
- `context`: Spring EL context prefix (default: "#root")
- `mappings`: Custom operator mappings (optional)

**Returns:**
- `str`: Spring EL string

**Example:**
```python
from mssql_to_spring_el.converter import to_spring_el

# Basic conversion
spring_el = to_spring_el(expression)

# Custom context
spring_el = to_spring_el(expression, context="#user")

# Custom operator mappings
mappings = {"=": " eq ", "!=": " ne "}
spring_el = to_spring_el(expression, mappings=mappings)
```

### Expression Classes

The library uses these AST classes to represent parsed expressions:

- **`Expression`**: Base class for all expressions
- **`BinaryOp`**: Binary operations (e.g., `age > 18`, `name AND active`)
- **`UnaryOp`**: Unary operations (e.g., `NOT active`)
- **`FunctionCall`**: Function calls (e.g., `ISNULL(name, 'Unknown')`)
- **`Literal`**: Literal values (e.g., `'John'`, `42`, `TRUE`)
- **`Variable`**: Column names/variables (e.g., `age`, `name`)
- **`Conditional`**: CASE expressions
- **`LogicalGroup`**: Parenthesized expressions

## Examples

### Basic Comparisons

```python
# SQL: WHERE age > 18
# Spring EL: #root.age > 18
parse_and_convert("WHERE age > 18")

# SQL: WHERE name = 'John'
# Spring EL: #root.name == 'John'
parse_and_convert("WHERE name = 'John'")
```

### Logical Operations

```python
# SQL: WHERE age > 18 AND status = 'active'
# Spring EL: #root.age > 18 and #root.status == 'active'
parse_and_convert("WHERE age > 18 AND status = 'active'")

# SQL: WHERE NOT (age < 18 OR status = 'inactive')
# Spring EL: not (#root.age < 18 or #root.status == 'inactive')
parse_and_convert("WHERE NOT (age < 18 OR status = 'inactive')")
```

### Advanced Features

```python
# SQL: WHERE name LIKE 'John%' AND age BETWEEN 18 AND 65
# Spring EL: #root.name matches 'John.*' and (#root.age >= 18 and #root.age <= 65)
parse_and_convert("WHERE name LIKE 'John%' AND age BETWEEN 18 AND 65")

# SQL: WHERE role IN ('admin', 'manager', 'user')
# Spring EL: {'admin', 'manager', 'user'}.contains(#root.role)
parse_and_convert("WHERE role IN ('admin', 'manager', 'user')")

# SQL: WHERE ISNULL(nickname, name) = 'John'
# Spring EL: (#root.nickname != null ? #root.nickname : #root.name) == 'John'
parse_and_convert("WHERE ISNULL(nickname, name) = 'John'")
```

## CLI Reference

```bash
python -m mssql_to_spring_el [OPTIONS] SQL_EXPRESSION

Options:
  --format FORMAT    Output format: 'text' or 'json' (default: text)
  --context CONTEXT  Spring EL context prefix (default: #root)
  --version         Show version information
  --help           Show help message

Examples:
  python -m mssql_to_spring_el "WHERE age > 18"
  python -m mssql_to_spring_el --format json "WHERE name LIKE 'John%'"
  python -m mssql_to_spring_el --context "#user" "WHERE role = 'admin'"
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=mssql_to_spring_el

# Run specific test file
pytest tests/test_parser_contract.py -v
```

### Project Structure

```
mssql_to_spring_el/
├── __init__.py          # Package initialization
├── __main__.py          # CLI entry point
├── main.py              # CLI implementation
├── logic_models.py      # AST class definitions
├── parser.py            # SQL parsing logic
└── converter.py         # Spring EL conversion logic

tests/
├── test_parser_contract.py     # Parser contract tests
├── test_converter_contract.py  # Converter contract tests
├── test_cli_contract.py        # CLI contract tests
├── test_integration_basic.py   # Basic integration tests
├── test_integration_complex.py # Complex integration tests
├── test_models.py              # Model unit tests
└── test_main.py                # Main function tests
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is licensed under the MIT License.
