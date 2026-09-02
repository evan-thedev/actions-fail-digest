# actions-fail-digest

Python CLI: turn noisy GitHub Actions failure logs into a compact text/Markdown/JSON digest.

## What it does

GitHub Actions logs are verbose — thousands of lines of timestamps, group markers, runner chatter, and successful step dumps. When a workflow fails, finding the actual error is tedious.

**actions-fail-digest** parses GHA logs (from files, directories, zips, or stdin) and extracts:

- Workflow and job name (when present)
- The failing step
- Primary error lines (cleaned of timestamps and noise)
- Context lines around errors
- GHA annotations (::error::, ::warning::, etc.)

It's aimed at UAT/CI debugging, not log warehousing. Works offline — no GitHub API or tokens required.

## What it is NOT

- Not a clone of [gha-fail-digest](https://github.com/johnsmith507/gha-fail-digest) (original implementation)
- Not a log warehouse or analytics platform
- Not for electronics/UAT diagnostic logs (see [fault-log](https://github.com/evan-thedev/fault-log) for that)
- Not for CSV test results (see [uat-summarizer](https://github.com/evan-thedev/uat-summarizer))

## Requirements

- Python 3.11+
- No external dependencies for core functionality
- `pytest` for running tests (optional)

## Installation

```bash
# Clone the repo
git clone https://github.com/evan-thedev/actions-fail-digest.git
cd actions-fail-digest

# Install in development mode
pip install -e .

# Or install with test dependencies
pip install -e ".[dev]"
```

## Usage

```bash
# Parse a single log file
actions-fail-digest workflow.log

# Parse from stdin
cat workflow.log | actions-fail-digest

# Parse a zip of logs
actions-fail-digest logs.zip

# Parse a directory of logs
actions-fail-digest logs/

# Output as JSON
actions-fail-digest --format json workflow.log

# Output as Markdown
actions-fail-digest --format markdown workflow.log

# Help
actions-fail-digest --help
```

## Example Output

Given this GHA log snippet:

```
2026-09-02T04:00:04.0000000Z ##[group]Run tests
2026-09-02T04:00:04.1234567Z Running: pytest tests/
2026-09-02T04:00:05.0000000Z ============================= test session starts ==============================
2026-09-02T04:00:05.1234567Z tests/test_parser.py::test_error_detection FAILED                       [ 40%]
2026-09-02T04:00:06.0000000Z 
2026-09-02T04:00:06.1234567Z     def test_error_detection():
2026-09-02T04:00:06.2345678Z         result = parse_log("test data")
2026-09-02T04:00:06.3456789Z >       assert result.has_failure == True
2026-09-02T04:00:06.4567890Z E       AssertionError: assert False == True
2026-09-02T04:00:07.2345678Z ::error::Test failed: test_error_detection
2026-09-02T04:00:08.0000000Z ========================= 1 failed, 4 passed in 2.45s ==========================
```

**Text output** (default):

```
Failing step: Run tests

Primary errors:
  tests/test_parser.py::test_error_detection FAILED                       [ 40%]
  E       AssertionError: assert False == True

Context:
  Running: pytest tests/
  ============================= test session starts ==============================
  tests/test_parser.py::test_error_detection FAILED                       [ 40%]
  def test_error_detection():
  result = parse_log("test data")

Annotations:
  [error] Test failed: test_error_detection
```

**JSON output** (`--format json`):

```json
{
  "workflow_name": null,
  "job_name": null,
  "failing_step": "Run tests",
  "error_lines": [
    "tests/test_parser.py::test_error_detection FAILED                       [ 40%]",
    "E       AssertionError: assert False == True"
  ],
  "context_lines": [
    "Running: pytest tests/",
    "============================= test session starts ==============================",
    "tests/test_parser.py::test_error_detection FAILED                       [ 40%]",
    "def test_error_detection():",
    "result = parse_log(\"test data\")"
  ],
  "annotations": [
    {
      "type": "error",
      "message": "Test failed: test_error_detection"
    }
  ],
  "has_failure": true
}
```

**Markdown output** (`--format markdown`):

```markdown
## GitHub Actions Failure Digest

**Failing step:** Run tests  

### Primary Errors

\```
tests/test_parser.py::test_error_detection FAILED                       [ 40%]
E       AssertionError: assert False == True
\```

### Context

\```
Running: pytest tests/
============================= test session starts ==============================
tests/test_parser.py::test_error_detection FAILED                       [ 40%]
def test_error_detection():
result = parse_log("test data")
\```

### Annotations

- **[error]** Test failed: test_error_detection
```

## Running Tests

```bash
# Install test dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=actions_fail_digest tests/
```

Tests run entirely offline — no network required.

## Exit Codes

- `0` — Successfully parsed and produced a digest (including "no failure found")
- `2` — Bad input or unreadable file

## Stack

- Python 3.11+
- Standard library only (no external runtime dependencies)
- pytest for testing

## License

MIT License. See [LICENSE](LICENSE) for details.

## Author

Evan Parrott  
GitHub: [@evan-thedev](https://github.com/evan-thedev)

## Contributing

Issues and PRs welcome. Please ensure tests pass before submitting.

## Related Projects

- [fault-log](https://github.com/evan-thedev/fault-log) — Electronics/UAT diagnostic log parser
- [uat-summarizer](https://github.com/evan-thedev/uat-summarizer) — CSV test result summarizer
