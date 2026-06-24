"""Deterministic text diff engine using Python difflib."""
import difflib
import hashlib


def compute_diff(old_text: str, new_text: str, context_lines: int = 3) -> str:
    """Compute unified diff between two config texts."""
    diff = difflib.unified_diff(
        old_text.splitlines(keepends=True),
        new_text.splitlines(keepends=True),
        fromfile="previous_config",
        tofile="current_config",
        n=context_lines,
    )
    return "".join(diff)


def compute_hash(text: str) -> str:
    """Compute SHA256 hash of config text."""
    return hashlib.sha256(text.encode()).hexdigest()


def compute_risk_level(diff_content: str) -> str:
    """Simple heuristic risk assessment for config changes.

    Returns: 'normal', 'suspicious', or 'high'
    """
    if not diff_content.strip():
        return "normal"

    added_lines = sum(1 for l in diff_content.splitlines() if l.startswith("+") and not l.startswith("+++"))
    removed_lines = sum(1 for l in diff_content.splitlines() if l.startswith("-") and not l.startswith("---"))

    dangerous_keywords = ["shutdown", "no ", "delete", "remove", "erase", "format", "reload"]
    has_dangerous = any(k in diff_content.lower() for k in dangerous_keywords)

    if has_dangerous:
        return "high"
    if added_lines + removed_lines > 20:
        return "suspicious"
    return "normal"
