#!/usr/bin/env python3
"""Tests for the one-line `run:` form in `scripts/check_action.py` (#66).

`run_blocks()` recognised only the block scalar, so a step written
`run: echo "${{ inputs.title }}"` never entered the list that `check()` walks: the same
expression SECURITY.md calls a shell injection through an input, and the checker silent.
Each case here puts one expression in one form and asks for the same refusal, so the two
spellings of `run:` are held to one rule. The block form is included because the change
must not move it.

Nothing here reaches the network or parses YAML, same as the checker.

Run: python3 -m unittest discover -s tests -t tests
"""

from __future__ import annotations

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout
from tempfile import TemporaryDirectory

from action_fixture import GOOD, action_file, check_action, line_of, mentions, problems


def step(run_line: str) -> str:
    """GOOD with one step appended whose body is the single `run:` line given."""
    return (
        GOOD
        + f"""
    - name: One line
      shell: bash
      run: {run_line}
"""
    )


class RunForms(unittest.TestCase):
    def test_block_form_expression_is_still_reported(self) -> None:
        # The control: the form that already worked keeps working, with the same wording.
        text = GOOD.replace('        echo "$CONFIG"', '        echo "${{ inputs.config }}"')
        found = problems(text)
        self.assertEqual(len(found), 1, found)
        self.assertIn("reaches the shell", found[0])

    def test_single_line_expression_is_reported_with_its_line(self) -> None:
        text = step('echo "${{ inputs.config }}"')
        found = problems(text)
        self.assertEqual(len(found), 1, found)
        self.assertIn("reaches the shell", found[0])
        self.assertIn(f"line {line_of(text, 'run: echo')}", found[0])

    def test_single_line_without_an_expression_is_accepted(self) -> None:
        # The shape is not the problem: only an expression reaching the shell is.
        self.assertEqual(problems(step('echo "nothing to add"')), [])

    def test_single_line_undeclared_input_is_reported_too(self) -> None:
        # `used` is collected from every run form, so an input that appears only in a
        # one-line run is still refused as undeclared, beside the interpolation problem.
        found = problems(step('echo "${{ inputs.extra }}"'))
        self.assertEqual(len(found), 2, found)
        self.assertTrue(mentions(found, "reaches the shell"))
        self.assertTrue(mentions(found, "extra is used in a run: block"))

    def test_quoted_single_line_expression_is_reported(self) -> None:
        self.assertTrue(
            mentions(problems(step('"echo ${{ inputs.config }}"')), "reaches the shell")
        )

    def test_main_exits_two_on_the_single_line_form(self) -> None:
        with TemporaryDirectory() as directory:
            broken = action_file(step('echo "${{ inputs.config }}"'), directory)
            errors = io.StringIO()
            with redirect_stdout(io.StringIO()), redirect_stderr(errors):
                self.assertEqual(check_action.main([str(broken)]), 2)
        self.assertIn("breaks 1 rule", errors.getvalue())


if __name__ == "__main__":
    unittest.main()
