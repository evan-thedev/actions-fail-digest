"""Tests for the log parser module."""

import json
from pathlib import Path

import pytest

from actions_fail_digest.parser import parse_log, LogDigest


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_parse_empty_log():
    """Test parsing an empty log."""
    digest = parse_log("")
    assert digest.workflow_name is None
    assert digest.job_name is None
    assert digest.failing_step is None
    assert not digest.has_failure
    assert len(digest.error_lines) == 0


def test_parse_sample_failure_log():
    """Test parsing a log with test failures."""
    log_content = (FIXTURES_DIR / "sample_failure.log").read_text()
    digest = parse_log(log_content)

    assert digest.has_failure
    assert digest.failing_step == "Run tests"
    assert any("AssertionError" in line or "assert" in line for line in digest.error_lines)
    assert len(digest.annotations) > 0
    assert any(ann["type"] == "error" for ann in digest.annotations)


def test_parse_build_error_log():
    """Test parsing a log with build errors."""
    log_content = (FIXTURES_DIR / "build_error.log").read_text()
    digest = parse_log(log_content)

    assert digest.has_failure
    assert digest.failing_step == "Build application"
    assert any("error" in line.lower() for line in digest.error_lines)
    assert len(digest.error_lines) > 0


def test_parse_success_log():
    """Test parsing a successful log with no failures."""
    log_content = (FIXTURES_DIR / "success.log").read_text()
    digest = parse_log(log_content)

    assert not digest.has_failure
    assert len(digest.error_lines) == 0


def test_annotation_parsing():
    """Test that GHA annotations are parsed correctly."""
    log_content = """
2026-09-02T04:00:00.0000000Z ##[group]Test step
2026-09-02T04:00:01.0000000Z ::error::File not found
2026-09-02T04:00:02.0000000Z ::warning::Deprecated API used
2026-09-02T04:00:03.0000000Z ::notice::Build completed
2026-09-02T04:00:04.0000000Z ##[endgroup]
"""
    digest = parse_log(log_content)

    assert len(digest.annotations) == 3
    assert digest.annotations[0]["type"] == "error"
    assert digest.annotations[0]["message"] == "File not found"
    assert digest.annotations[1]["type"] == "warning"
    assert digest.annotations[2]["type"] == "notice"
    assert digest.has_failure


def test_text_output_format():
    """Test text formatting of digest."""
    digest = LogDigest(
        workflow_name="CI",
        job_name="test",
        failing_step="Run tests",
        error_lines=["Error: test failed"],
        has_failure=True,
    )

    text = digest.to_text()
    assert "Workflow: CI" in text
    assert "Job: test" in text
    assert "Failing step: Run tests" in text
    assert "Error: test failed" in text


def test_markdown_output_format():
    """Test Markdown formatting of digest."""
    digest = LogDigest(
        workflow_name="CI",
        job_name="test",
        failing_step="Run tests",
        error_lines=["Error: test failed"],
        has_failure=True,
    )

    markdown = digest.to_markdown()
    assert "## GitHub Actions Failure Digest" in markdown
    assert "**Workflow:** CI" in markdown
    assert "**Job:** test" in markdown
    assert "**Failing step:** Run tests" in markdown
    assert "Error: test failed" in markdown


def test_json_output_format():
    """Test JSON formatting of digest."""
    digest = LogDigest(
        workflow_name="CI",
        job_name="test",
        failing_step="Run tests",
        error_lines=["Error: test failed"],
        annotations=[{"type": "error", "message": "Test failed"}],
        has_failure=True,
    )

    data = digest.to_dict()
    assert data["workflow_name"] == "CI"
    assert data["job_name"] == "test"
    assert data["failing_step"] == "Run tests"
    assert data["has_failure"] is True
    assert len(data["error_lines"]) == 1
    assert len(data["annotations"]) == 1

    json_str = json.dumps(data)
    assert "CI" in json_str
    assert "test" in json_str


def test_no_failure_text_output():
    """Test text output when no failure is detected."""
    digest = LogDigest(has_failure=False)
    text = digest.to_text()
    assert "No failure detected" in text


def test_context_lines_extracted():
    """Test that context lines around errors are extracted."""
    log_content = """
2026-09-02T04:00:00.0000000Z Line before error
2026-09-02T04:00:01.0000000Z This line has an error: something failed
2026-09-02T04:00:02.0000000Z Line after error
"""
    digest = parse_log(log_content)

    assert digest.has_failure
    assert len(digest.context_lines) > 0
    assert any("error" in line.lower() for line in digest.context_lines)


def test_timestamp_stripping():
    """Test that timestamps are stripped from output."""
    log_content = "2026-09-02T04:00:00.0000000Z Error: test failed"
    digest = parse_log(log_content)

    assert digest.has_failure
    assert any("Error: test failed" in line for line in digest.error_lines)
    assert not any("2026-09-02T" in line for line in digest.error_lines)


def test_group_markers_ignored():
    """Test that group markers don't appear in error lines."""
    log_content = """
##[group]Test step
Error: something went wrong
##[endgroup]
"""
    digest = parse_log(log_content)

    assert digest.has_failure
    assert not any("##[" in line for line in digest.error_lines)


def test_multiple_error_patterns():
    """Test detection of various error patterns."""
    error_patterns = [
        "Error: file not found",
        "FAILED tests/test_foo.py",
        "Failure in module",
        "Exception occurred",
        "Fatal: cannot proceed",
        "Unable to complete operation",
    ]

    for pattern in error_patterns:
        digest = parse_log(pattern)
        assert digest.has_failure, f"Failed to detect error in: {pattern}"
