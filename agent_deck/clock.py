"""Time — one standardized timestamp format for the whole app.

Every stored timestamp is an ISO-8601 UTC string (JSON-portable, sorts
lexicographically, means the same thing in any store or timezone). Produce
timestamps only through here so the format never drifts between records.
"""

from __future__ import annotations

from datetime import datetime, timezone


def now_iso() -> str:
    """Return the current UTC instant as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
