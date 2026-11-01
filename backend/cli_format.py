"""Terminal formatting utilities for CLI commands.

Provides ASCII box drawing and table formatting without external dependencies.
Safe for Windows PowerShell 5.1 and UTF-8 / ASCII consoles.
"""
from __future__ import annotations

import sys
from typing import Any, Sequence


def print_box(
    title: str,
    items: list[tuple[str, Any]],
    min_width: int = 40,
    file=None,
) -> None:
    """Print an ASCII bordered box with key-value pairs aligned.

    Example:
        +-- Session started ----------------+
        | Session ID   : 3                  |
        | Course ID    : 1                  |
        | Late after   : 10 min             |
        +-----------------------------------+
    """
    out = file if file is not None else sys.stdout

    if not items:
        content_width = max(min_width - 4, len(title) + 4)
        total_width = content_width + 4
        dash_count = max(0, total_width - len(title) - 6)
        top = f"+-- {title} " + ("-" * dash_count) + "+"
        bottom = "+" + ("-" * (total_width - 2)) + "+"
        print(top, file=out)
        print(bottom, file=out)
        return

    max_k = max(len(str(k)) for k, _ in items)
    max_v = max(len(str(v)) for _, v in items)
    content_width = max(min_width - 4, len(title) + 4, max_k + max_v + 5)
    total_width = content_width + 4

    dash_count = max(0, total_width - len(title) - 6)
    top = f"+-- {title} " + ("-" * dash_count) + "+"
    bottom = "+" + ("-" * (total_width - 2)) + "+"

    print(top, file=out)
    for k, v in items:
        line_content = f"{str(k):<{max_k}} : {str(v)}"
        padded = f"| {line_content:<{content_width}} |"
        print(padded, file=out)
    print(bottom, file=out)


def print_table(
    headers: list[str],
    rows: list[list[Any]],
    file=None,
) -> None:
    """Print a clean ASCII table with column headers and borders.

    Example:
        +------------+------------------+------+--------+-----------+
        | Student ID | Major            | Term | Photos | Embedding |
        +------------+------------------+------+--------+-----------+
        | S1001      | Computer Science | 4    | 4      | Yes       |
        +------------+------------------+------+--------+-----------+
    """
    out = file if file is not None else sys.stdout
    if not headers:
        return

    col_count = len(headers)
    col_widths = [len(str(h)) for h in headers]
    for row in rows:
        for idx in range(min(col_count, len(row))):
            col_widths[idx] = max(col_widths[idx], len(str(row[idx])))

    border = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
    header_line = "| " + " | ".join(f"{str(h):<{w}}" for h, w in zip(headers, col_widths)) + " |"

    print(border, file=out)
    print(header_line, file=out)
    print(border, file=out)
    for row in rows:
        padded_row = list(row) + [""] * (col_count - len(row))
        row_line = "| " + " | ".join(f"{str(cell):<{w}}" for cell, w in zip(padded_row, col_widths)) + " |"
        print(row_line, file=out)
    print(border, file=out)

