#!/usr/bin/env python3
"""Fixture helpers shared by the `scripts/check_action.py` test modules.

The action file the checker is exercised against lives in `test_check_action.py` as `GOOD`,
because that suite is what grew it. The three later suites (#66, #67, #68) each mutate one
rule of the same file, so this module re-exports it rather than keep a second copy that can
drift: one `GOOD`, one write-and-check helper, one way to name a line.

It is deliberately not named `test_*.py`: `unittest discover` skips it, and importing a test
class into another module would run that class's cases a second time.

Run: python3 -m unittest discover -s tests -t tests
"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from test_check_action import CHECKOUT, GOOD, check_action

__all__ = ["CHECKOUT", "GOOD", "action_file", "check_action", "line_of", "mentions", "problems"]


def action_file(text: str, directory: str) -> Path:
    """Write `text` into `directory` where the checker can read it as an action file."""
    path = Path(directory) / "action.yml"
    path.write_text(text, encoding="utf-8")
    return path


def problems(text: str) -> list[str]:
    with TemporaryDirectory() as directory:
        return check_action.check(action_file(text, directory))


def mentions(problems: list[str], needle: str) -> list[str]:
    return [line for line in problems if needle in line]


def line_of(text: str, needle: str) -> int:
    """The 1-based line number of the single line of `text` containing `needle`."""
    matches = [number for number, line in enumerate(text.splitlines(), start=1) if needle in line]
    if len(matches) != 1:
        raise AssertionError(f"{needle!r} appears on {len(matches)} lines, expected 1")
    return matches[0]
