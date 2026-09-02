"""Actions Fail Digest - GitHub Actions log parser and failure digest generator."""

__version__ = "0.1.0"

from .parser import parse_log, LogDigest

__all__ = ["parse_log", "LogDigest"]
