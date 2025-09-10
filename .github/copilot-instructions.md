- [x] Verify that the copilot-instructions.md file in the .github directory is created. Completed: File created.

- [x] Clarify Project Requirements Completed: Project type is Python library.

- [x] Scaffold the Project Completed: Created basic Python library structure with package, tests, pyproject.toml, README, .gitignore.

- [x] Customize the Project Skipped: Basic "Hello World" library.

- [x] Install Required Extensions Skipped: No extensions specified.

- [x] Compile the Project Completed: Python environment configured, pytest installed.

- [x] Create and Run Task Completed: Created test task, ran tests successfully.

- [x] Launch the Project Skipped: No launch for library.

- [x] Ensure Documentation is Complete Completed: README and instructions exist.

- Work through each checklist item systematically.
- Keep communication concise and focused.
- Follow development best practices.

## MSSQL Logic Parser Feature Instructions

### Project Overview
This is a Python library that parses MSSQL (T-SQL) logical expressions and converts them to Spring Expression Language (Spring EL).

### Key Components
- `mylibrary/logic_models.py`: Object model classes for expressions
- `mylibrary/parser.py`: Parser for MSSQL logic strings
- `mylibrary/converter.py`: Converter to Spring EL
- `mylibrary/main.py`: CLI interface
- `tests/`: Unit and integration tests

### Development Guidelines
- Follow TDD: Write tests before implementation
- Use type hints in all Python code
- Include docstrings for all functions and classes
- Handle errors gracefully with custom exceptions
- Use logging for debugging and monitoring

### Coding Standards
- PEP 8 compliant
- Maximum line length: 88 characters
- Use descriptive variable names
- Add comments for complex logic

### Testing Requirements
- Unit tests for all functions
- Integration tests for end-to-end conversion
- Test edge cases and error conditions
- Use pytest framework

### Documentation
- Update README.md with usage examples
- Include API documentation
- Add inline comments for complex algorithms

### Current Feature: MSSQL Logic Parser to Spring EL Converter
- Parse WHERE/HAVING clauses, CASE statements
- Support logical operators: AND, OR, NOT
- Support comparisons: =, >, <, LIKE, IN
- Convert to Spring EL syntax
- CLI interface for easy usage

### Implementation Steps
1. Design object model in logic_models.py
2. Implement parser in parser.py
3. Implement converter in converter.py
4. Update main.py for CLI
5. Write comprehensive tests
6. Update documentation

### Dependencies
- sqlparse: For SQL tokenization
- pyparsing: For custom grammar parsing
- pytest: For testing

### Output Formats
- Text: Human-readable Spring EL
- JSON: Structured data with parsed model and EL string
