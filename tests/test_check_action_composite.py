#!/usr/bin/env python3
"""Tests for the two shape rules in `scripts/check_action.py` (#68).

`action.yml` is composite and every step that runs names `shell: bash`. Neither key was
ever read: `check()` covered inputs, run bodies, env bindings, pins and step ids, so
switching `using` to `node20` — which changes what every `run:` line means — would pass
every other rule, and a step without a shell is only refused by the runner, after a
consumer has adopted the tag. Both are line scans over the text the checker already has.

Presence is the assertion, not an allowlist of shells: the check asks that a step naming a
`run:` also names a `shell:`, and says nothing about which shell.

Run: python3 -m unittest discover -s tests -t tests
"""

from __future__ import annotations

import unittest
from pathlib import Path

from action_fixture import GOOD, check_action, line_of, problems

ROOT = Path(__file__).resolve().parent.parent


class CompositeShape(unittest.TestCase):
    def test_the_shipped_file_holds_both_shapes(self) -> None:
        self.assertEqual(check_action.check(ROOT / "action.yml"), [])

    def test_a_non_composite_using_is_refused(self) -> None:
        text = GOOD.replace("  using: composite", "  using: node20")
        found = problems(text)
        self.assertEqual(len(found), 1, found)
        self.assertIn("and this action is composite", found[0])
        self.assertIn(f"line {line_of(text, 'using: node20')}", found[0])

    def test_a_missing_using_is_refused(self) -> None:
        text = GOOD.replace("  using: composite\n", "")
        found = problems(text)
        self.assertEqual(len(found), 1, found)
        self.assertIn("declares no using:", found[0])

    def test_a_run_step_without_a_shell_is_refused(self) -> None:
        text = GOOD.replace(
            "    - name: Run the audit\n      id: audit\n      shell: bash\n",
            "    - name: Run the audit\n      id: audit\n",
        )
        found = problems(text)
        self.assertEqual(len(found), 1, found)
        self.assertIn("without a shell:", found[0])
        self.assertIn(f"line {line_of(text, '- name: Run the audit')}", found[0])

    def test_a_uses_only_step_carries_no_shell_requirement(self) -> None:
        # The pin rule still reads this step and the shell rule stays silent on it: only a
        # step with a run: is a step that has to name a shell.
        step = GOOD.split("    - name: Fetch Gauge\n", 1)[1].split("\n    - name:", 1)[0]
        self.assertIn("uses:", step)
        self.assertNotIn("shell:", step)
        self.assertNotIn("run:", step)
        self.assertEqual(problems(GOOD), [])

    def test_the_single_line_form_is_a_step_that_runs(self) -> None:
        # #66 taught `run_blocks` the one-line form; this rule has to see it too, or the new
        # spelling becomes a way around the shell requirement.
        text = GOOD.replace(
            "      id: audit\n      shell: bash\n"
            '      run: |\n        echo "exit-code=0" >> "$GITHUB_OUTPUT"',
            '      id: audit\n      run: echo "exit-code=0" >> "$GITHUB_OUTPUT"',
        )
        found = problems(text)
        self.assertEqual(len(found), 1, found)
        self.assertIn("without a shell:", found[0])

    def test_a_one_line_step_that_names_its_shell_is_clean(self) -> None:
        text = GOOD.replace(
            '      run: |\n        echo "exit-code=0" >> "$GITHUB_OUTPUT"',
            '      run: echo "exit-code=0" >> "$GITHUB_OUTPUT"',
        )
        self.assertEqual(problems(text), [])


if __name__ == "__main__":
    unittest.main()
