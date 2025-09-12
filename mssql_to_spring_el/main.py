"""
CLI interface for MSSQL Logic Parser.

Usage:
    python -m mylibrary "WHERE age > 18 AND status = 'active'"
    python -m mylibrary --format json "WHERE age > 18"
    python -m mylibrary --context "#user" "WHERE age > 18"
"""

import argparse
import json
import sys
from mssql_to_spring_el.parser import parse_sql_logic
from mssql_to_spring_el.converter import to_spring_el


def main():
    """
    Main CLI entry point for MSSQL Logic Parser.
    
    Provides command-line interface for parsing MSSQL logical expressions
    and converting them to Spring Expression Language (SpEL) format.
    
    Command-line arguments:
        sql_logic: MSSQL logical expression to parse (positional argument)
        --format: Output format ('text' or 'json', default: 'text')
        --context: Spring EL context prefix (default: '#root')
        --version: Show version information and exit
        --help: Show help message and exit
    
    Examples:
        python -m mylibrary "WHERE age > 18 AND status = 'active'"
        python -m mylibrary --format json "WHERE name LIKE 'John%'"
        python -m mylibrary --context "#user" "WHERE role = 'admin'"
        python -m mylibrary --version
    
    Exit codes:
        0: Success
        1: Invalid arguments or parsing error
        2: Conversion error
    """
    parser = argparse.ArgumentParser(
        description="Parse MSSQL logic expressions and convert to Spring EL"
    )
    parser.add_argument(
        'sql_logic',
        nargs='?',
        help="MSSQL logic string to parse and convert"
    )
    parser.add_argument(
        '--format',
        choices=['text', 'json'],
        default='text',
        help="Output format (default: text)"
    )
    parser.add_argument(
        '--context',
        default='#root',
        help="Spring EL context prefix (default: #root)"
    )
    parser.add_argument(
        '--version',
        action='version',
        version='mylibrary 1.0.0',
        help="Show version information"
    )

    args = parser.parse_args()

    # If no SQL logic provided, show help
    if not args.sql_logic:
        parser.print_help()
        return

    try:
        # Parse the SQL logic
        expression = parse_sql_logic(args.sql_logic)

        # Convert to Spring EL
        el_string = to_spring_el(expression, context=args.context)

        if args.format == 'json':
            result = {
                'input': args.sql_logic,
                'parsed': expression.to_dict(),
                'spring_el': el_string
            }
            print(json.dumps(result, indent=2))
        else:
            print(f"Spring EL: {el_string}")

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == '__main__':
    main()
