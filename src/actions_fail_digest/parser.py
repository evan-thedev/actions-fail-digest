"""GitHub Actions log parser and digest generator."""

import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LogDigest:
    """Structured representation of a GitHub Actions log digest."""

    workflow_name: Optional[str] = None
    job_name: Optional[str] = None
    failing_step: Optional[str] = None
    error_lines: list[str] = field(default_factory=list)
    context_lines: list[str] = field(default_factory=list)
    annotations: list[dict[str, str]] = field(default_factory=list)
    has_failure: bool = False

    def to_text(self) -> str:
        """Format digest as human-readable text."""
        lines = []

        if self.workflow_name:
            lines.append(f"Workflow: {self.workflow_name}")
        if self.job_name:
            lines.append(f"Job: {self.job_name}")
        if self.failing_step:
            lines.append(f"Failing step: {self.failing_step}")

        if self.error_lines:
            lines.append("\nPrimary errors:")
            for error in self.error_lines:
                lines.append(f"  {error}")

        if self.context_lines:
            lines.append("\nContext:")
            for ctx in self.context_lines:
                lines.append(f"  {ctx}")

        if self.annotations:
            lines.append("\nAnnotations:")
            for ann in self.annotations:
                ann_type = ann.get("type", "unknown")
                message = ann.get("message", "")
                lines.append(f"  [{ann_type}] {message}")

        if not self.has_failure:
            lines.append("No failure detected in log")

        return "\n".join(lines) if lines else "Empty log or no parseable content"

    def to_markdown(self) -> str:
        """Format digest as Markdown."""
        lines = []

        if self.workflow_name or self.job_name:
            lines.append("## GitHub Actions Failure Digest\n")
            if self.workflow_name:
                lines.append(f"**Workflow:** {self.workflow_name}  ")
            if self.job_name:
                lines.append(f"**Job:** {self.job_name}  ")
            if self.failing_step:
                lines.append(f"**Failing step:** {self.failing_step}  ")
            lines.append("")

        if self.error_lines:
            lines.append("### Primary Errors\n")
            lines.append("```")
            lines.extend(self.error_lines)
            lines.append("```\n")

        if self.context_lines:
            lines.append("### Context\n")
            lines.append("```")
            lines.extend(self.context_lines)
            lines.append("```\n")

        if self.annotations:
            lines.append("### Annotations\n")
            for ann in self.annotations:
                ann_type = ann.get("type", "unknown")
                message = ann.get("message", "")
                lines.append(f"- **[{ann_type}]** {message}")
            lines.append("")

        if not self.has_failure:
            lines.append("_No failure detected in log_")

        return "\n".join(lines) if lines else "_Empty log or no parseable content_"

    def to_dict(self) -> dict:
        """Format digest as a dictionary (suitable for JSON serialization)."""
        return {
            "workflow_name": self.workflow_name,
            "job_name": self.job_name,
            "failing_step": self.failing_step,
            "error_lines": self.error_lines,
            "context_lines": self.context_lines,
            "annotations": self.annotations,
            "has_failure": self.has_failure,
        }


def parse_log(content: str) -> LogDigest:
    """
    Parse a GitHub Actions log and extract failure digest.

    Args:
        content: Raw log content as string

    Returns:
        LogDigest object containing parsed information
    """
    digest = LogDigest()

    lines = content.splitlines()
    if not lines:
        return digest

    in_group = False
    current_step = None
    error_context = []
    found_error = False

    annotation_pattern = re.compile(r"::(error|warning|notice)::(.*)")
    timestamp_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z\s+")
    group_start_pattern = re.compile(r"##\[group\](.*)")
    group_end_pattern = re.compile(r"##\[endgroup\]")

    error_keywords = [
        "error:",
        "failed",
        "failure",
        "exception",
        "traceback",
        "fatal:",
        "err:",
        "cannot",
        "unable to",
    ]

    for i, line in enumerate(lines):
        stripped = line.strip()

        clean_line = timestamp_pattern.sub("", line).strip()

        if match := annotation_pattern.search(clean_line):
            ann_type = match.group(1)
            ann_message = match.group(2).strip()
            digest.annotations.append({"type": ann_type, "message": ann_message})
            if ann_type == "error":
                digest.has_failure = True
                if ann_message and ann_message not in digest.error_lines:
                    digest.error_lines.append(ann_message)
            continue

        if match := group_start_pattern.search(clean_line):
            in_group = True
            current_step = match.group(1).strip()
            continue

        if group_end_pattern.search(clean_line):
            in_group = False
            continue

        if not stripped or stripped.startswith("##["):
            continue

        lower_line = clean_line.lower()
        if any(keyword in lower_line for keyword in error_keywords):
            digest.has_failure = True
            found_error = True

            if not digest.failing_step and current_step:
                digest.failing_step = current_step

            if clean_line and clean_line not in digest.error_lines:
                digest.error_lines.append(clean_line[:200])

            start = max(0, i - 2)
            end = min(len(lines), i + 3)
            for j in range(start, end):
                ctx_line = timestamp_pattern.sub("", lines[j]).strip()
                if ctx_line and not ctx_line.startswith("##[") and len(digest.context_lines) < 10:
                    if ctx_line not in digest.context_lines:
                        digest.context_lines.append(ctx_line[:200])

    for line in lines[:50]:
        if "workflow" in line.lower() and not digest.workflow_name:
            parts = line.split("workflow", 1)
            if len(parts) > 1:
                potential = parts[1].strip().strip(":").strip()
                if potential and len(potential) < 100:
                    digest.workflow_name = potential
                    break

    if not digest.job_name:
        for line in lines[:50]:
            if re.search(r"\bjob\b", line, re.IGNORECASE):
                parts = re.split(r"\bjob\b", line, 1, re.IGNORECASE)
                if len(parts) > 1:
                    potential = parts[1].strip().strip(":").strip()
                    if potential and len(potential) < 100:
                        digest.job_name = potential
                        break

    return digest
