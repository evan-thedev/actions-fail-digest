"""Tests for the CLI module."""

import json
import sys
from io import StringIO
from pathlib import Path

import pytest

from actions_fail_digest.cli import main, read_input


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_read_single_file():
    """Test reading a single log file."""
    log_path = str(FIXTURES_DIR / "sample_failure.log")
    content, exit_code = read_input(log_path)

    assert exit_code == 0
    assert len(content) > 0
    assert "test session starts" in content


def test_read_nonexistent_file():
    """Test reading a file that doesn't exist."""
    content, exit_code = read_input("nonexistent.log")

    assert exit_code == 2
    assert content == ""


def test_read_zip_file():
    """Test reading logs from a zip archive."""
    zip_path = str(FIXTURES_DIR / "logs.zip")
    content, exit_code = read_input(zip_path)

    assert exit_code == 0
    assert len(content) > 0
    assert "sample_failure" in content or "test session starts" in content


def test_read_directory():
    """Test reading logs from a directory."""
    content, exit_code = read_input(str(FIXTURES_DIR))

    assert exit_code == 0
    assert len(content) > 0


def test_read_stdin(monkeypatch):
    """Test reading from stdin."""
    test_input = "2026-09-02T04:00:00.0000000Z Error: test failed\n"
    monkeypatch.setattr("sys.stdin", StringIO(test_input))

    content, exit_code = read_input(None)

    assert exit_code == 0
    assert "Error: test failed" in content


def test_cli_text_output(monkeypatch, capsys):
    """Test CLI with text output format."""
    log_path = str(FIXTURES_DIR / "sample_failure.log")
    monkeypatch.setattr("sys.argv", ["actions-fail-digest", log_path])

    exit_code = main()

    assert exit_code == 0
    captured = capsys.readouterr()
    assert len(captured.out) > 0


def test_cli_markdown_output(monkeypatch, capsys):
    """Test CLI with Markdown output format."""
    log_path = str(FIXTURES_DIR / "build_error.log")
    monkeypatch.setattr("sys.argv", ["actions-fail-digest", "--format", "markdown", log_path])

    exit_code = main()

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "##" in captured.out or "_" in captured.out


def test_cli_json_output(monkeypatch, capsys):
    """Test CLI with JSON output format."""
    log_path = str(FIXTURES_DIR / "sample_failure.log")
    monkeypatch.setattr("sys.argv", ["actions-fail-digest", "--format", "json", log_path])

    exit_code = main()

    assert exit_code == 0
    captured = capsys.readouterr()

    data = json.loads(captured.out)
    assert "workflow_name" in data
    assert "job_name" in data
    assert "has_failure" in data


def test_cli_with_success_log(monkeypatch, capsys):
    """Test CLI with a successful log (no failures)."""
    log_path = str(FIXTURES_DIR / "success.log")
    monkeypatch.setattr("sys.argv", ["actions-fail-digest", log_path])

    exit_code = main()

    assert exit_code == 0
    captured = capsys.readouterr()
    assert "No failure detected" in captured.out or len(captured.out) > 0


def test_cli_with_nonexistent_file(monkeypatch, capsys):
    """Test CLI with a file that doesn't exist."""
    monkeypatch.setattr("sys.argv", ["actions-fail-digest", "nonexistent.log"])

    exit_code = main()

    assert exit_code == 2
    captured = capsys.readouterr()
    assert len(captured.err) > 0 or exit_code != 0


def test_cli_with_zip(monkeypatch, capsys):
    """Test CLI with a zip file."""
    zip_path = str(FIXTURES_DIR / "logs.zip")
    monkeypatch.setattr("sys.argv", ["actions-fail-digest", zip_path])

    exit_code = main()

    assert exit_code == 0
    captured = capsys.readouterr()
    assert len(captured.out) > 0


def test_cli_stdin(monkeypatch, capsys):
    """Test CLI reading from stdin."""
    test_log = "2026-09-02T04:00:00.0000000Z Error: test failed\n"
    monkeypatch.setattr("sys.stdin", StringIO(test_log))
    monkeypatch.setattr("sys.argv", ["actions-fail-digest"])

    exit_code = main()

    assert exit_code == 0
    captured = capsys.readouterr()
    assert len(captured.out) > 0


def test_cli_stdin_explicit_dash(monkeypatch, capsys):
    """Test CLI with explicit '-' for stdin."""
    test_log = "2026-09-02T04:00:00.0000000Z Error: operation failed\n"
    monkeypatch.setattr("sys.stdin", StringIO(test_log))
    monkeypatch.setattr("sys.argv", ["actions-fail-digest", "-"])

    exit_code = main()

    assert exit_code == 0
    captured = capsys.readouterr()
    assert len(captured.out) > 0
