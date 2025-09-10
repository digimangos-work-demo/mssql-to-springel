import pytest
from mylibrary.main import main
import sys
from io import StringIO


def test_main_simple(monkeypatch, capsys):
    """Test main function with simple input."""
    # Mock command line arguments
    test_args = ["mylibrary", "WHERE age > 18"]
    monkeypatch.setattr(sys, 'argv', test_args)

    main()

    captured = capsys.readouterr()
    assert "Spring EL: #root.age > 18" in captured.out


def test_main_json_format(monkeypatch, capsys):
    """Test main function with JSON format."""
    test_args = ["mylibrary", "--format", "json", "WHERE age > 18"]
    monkeypatch.setattr(sys, 'argv', test_args)

    main()

    captured = capsys.readouterr()
    assert '"spring_el": "#root.age > 18"' in captured.out
    assert '"input": "WHERE age > 18"' in captured.out
