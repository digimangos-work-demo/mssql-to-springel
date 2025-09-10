import subprocess
import json
import pytest
import sys


def test_cli_basic_usage():
    """Test basic CLI usage."""
    result = subprocess.run(
        [sys.executable, "-m", "mylibrary", "WHERE age > 18"],
        capture_output=True,
        text=True,
        cwd="/Users/digimangos/test"
    )
    
    # Should succeed once implemented
    assert result.returncode == 0
    assert "Spring EL:" in result.stdout


def test_cli_help():
    """Test CLI help option."""
    result = subprocess.run(
        [sys.executable, "-m", "mylibrary", "--help"],
        capture_output=True,
        text=True,
        cwd="/Users/digimangos/test"
    )
    
    # Help should work even if not fully implemented
    assert "--help" in result.stdout or "--help" in result.stderr


def test_cli_version():
    """Test CLI version option."""
    result = subprocess.run(
        [sys.executable, "-m", "mylibrary", "--version"],
        capture_output=True,
        text=True,
        cwd="/Users/digimangos/test"
    )
    
    # Version should work
    assert result.returncode == 0 or "version" in result.stdout.lower()


def test_cli_invalid_arguments():
    """Test CLI with invalid arguments."""
    result = subprocess.run(
        [sys.executable, "-m", "mylibrary", "--invalid"],
        capture_output=True,
        text=True,
        cwd="/Users/digimangos/test"
    )
    
    # Should return exit code 2 for invalid arguments
    assert result.returncode != 0


def test_cli_missing_sql():
    """Test CLI without SQL argument."""
    result = subprocess.run(
        [sys.executable, "-m", "mylibrary"],
        capture_output=True,
        text=True,
        cwd="/Users/digimangos/test"
    )
    
    # Should show help when no SQL provided
    assert result.returncode == 0
    assert "usage:" in result.stdout


def test_cli_format_json():
    """Test JSON output format."""
    result = subprocess.run(
        [sys.executable, "-m", "mylibrary", "--format", "json", "WHERE age > 18"],
        capture_output=True,
        text=True,
        cwd="/Users/digimangos/test"
    )
    
    # Should succeed with JSON output
    assert result.returncode == 0
    
    # Check JSON output
    try:
        import json
        data = json.loads(result.stdout)
        assert "input" in data
        assert "spring_el" in data
        assert "parsed" in data
    except json.JSONDecodeError:
        pytest.fail("Output is not valid JSON")


def test_cli_custom_context():
    """Test custom context option."""
    result = subprocess.run(
        [sys.executable, "-m", "mylibrary", "--context", "#user", "WHERE age > 18"],
        capture_output=True,
        text=True,
        cwd="/Users/digimangos/test"
    )
    
    # Should succeed with custom context
    assert result.returncode == 0
    assert "#user.age > 18" in result.stdout
