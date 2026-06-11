from __future__ import annotations

import re


def normalize_direction(direction: str) -> str:
    """Normalize EFA direction strings to a consistent format."""
    direction = re.sub(r'^Aschaffenburg\s*[,;]\s*', '', direction).strip()
    direction = re.sub(r'\s*/\s*', '/', direction)
    direction = re.sub(r'\s*;\s*', '; ', direction)
    return direction


def sort_lines(lines: list[str]) -> list[str]:
    """Sort line numbers: numeric first, then alpha."""
    return sorted(lines, key=lambda x: (not x.isdigit(), x.zfill(5) if x.isdigit() else x))
