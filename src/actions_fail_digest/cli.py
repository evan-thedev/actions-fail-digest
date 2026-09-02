"""Command-line interface for Actions Fail Digest."""

import argparse
import json
import sys
import zipfile
from pathlib import Path
from typing import Optional

from .parser import parse_log


def read_input(input_path: Optional[str]) -> tuple[str, int]:
    """
    Read log content from file, directory, zip, or stdin.

    Returns:
        Tuple of (content, exit_code)
    """
    if input_path is None or input_path == "-":
        try:
            content = sys.stdin.read()
            return content, 0
        except Exception as e:
            print(f"Error reading from stdin: {e}", file=sys.stderr)
            return "", 2

    path = Path(input_path)

    if not path.exists():
        print(f"Error: Path does not exist: {input_path}", file=sys.stderr)
        return "", 2

    try:
        if path.is_file():
            if path.suffix == ".zip":
                contents = []
                with zipfile.ZipFile(path, "r") as zf:
                    for name in zf.namelist():
                        if name.endswith((".txt", ".log")):
                            with zf.open(name) as f:
                                contents.append(f.read().decode("utf-8", errors="replace"))
                return "\n".join(contents), 0
            else:
                return path.read_text(encoding="utf-8", errors="replace"), 0

        elif path.is_dir():
            contents = []
            for log_file in sorted(path.glob("**/*.txt")) + sorted(path.glob("**/*.log")):
                if log_file.is_file():
                    contents.append(log_file.read_text(encoding="utf-8", errors="replace"))
            return "\n".join(contents), 0

        else:
            print(f"Error: Not a file or directory: {input_path}", file=sys.stderr)
            return "", 2

    except Exception as e:
        print(f"Error reading input: {e}", file=sys.stderr)
        return "", 2


def main() -> int:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        prog="actions-fail-digest",
        description="Parse GitHub Actions logs and produce compact failure digests",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Parse a single log file
  actions-fail-digest workflow.log

  # Parse from stdin
  cat workflow.log | actions-fail-digest

  # Parse a zip of logs
  actions-fail-digest logs.zip

  # Output as JSON
  actions-fail-digest --format json workflow.log

  # Output as Markdown
  actions-fail-digest --format markdown workflow.log
        """,
    )

    parser.add_argument(
        "input",
        nargs="?",
        help="Log file, directory, zip archive, or '-' for stdin (default: stdin)",
    )

    parser.add_argument(
        "--format",
        choices=["text", "markdown", "json"],
        default="text",
        help="Output format (default: text)",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )

    args = parser.parse_args()

    content, read_exit = read_input(args.input)
    if read_exit != 0:
        return read_exit

    digest = parse_log(content)

    if args.format == "json":
        print(json.dumps(digest.to_dict(), indent=2))
    elif args.format == "markdown":
        print(digest.to_markdown())
    else:
        print(digest.to_text())

    return 0


if __name__ == "__main__":
    sys.exit(main())
