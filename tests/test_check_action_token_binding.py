#!/usr/bin/env python3
"""Tests for the `github-token` binding rule in `scripts/check_action.py` (#67).

The checker requires every declared input to appear in some step's `env:` mapping, then
skipped one name: `github-token`. That exemption was written when the token was only
described in prose; `action.yml` now binds it twice, so the carve-out no longer permits
anything real and only hides the regression it was written to permit — a token declared and
reaching no step, which would fail at the issue API instead of at the gate.

The rule is about binding, not the value: the token appearing in one step's environment is
enough, and no environment variable name is special. Each case mutates the `GOOD` fixture so
a reviewer can see the one difference that matters.

Run: python3 -m unittest discover -s tests -t tests
"""

from __future__ import annotations

import unittest
from pathlib import Path

from action_fixture import GOOD, check_action, mentions, problems

ROOT = Path(__file__).resolve().parent.parent
TOKEN_BINDING = "        TOKEN: ${{ inputs.github-token }}\n"
UNBOUND = GOOD.replace(TOKEN_BINDING, "")


class TokenBinding(unittest.TestCase):
    def test_the_shipped_file_needs_no_exemption(self) -> None:
        # The premise of the change: the real action already satisfies the rule on its own.
        self.assertEqual(check_action.check(ROOT / "action.yml"), [])

    def test_declared_but_unbound_token_is_reported(self) -> None:
        found = problems(UNBOUND)
        self.assertEqual(len(found), 1, found)
        self.assertIn("github-token is declared but never bound", found[0])

    def test_token_bound_in_one_step_is_enough(self) -> None:
        # The variable is called TOKEN here, which is the point: the check reads what the
        # mapping binds, not a name on an allowlist.
        self.assertEqual(problems(GOOD), [])

    def test_token_used_in_a_run_counts_as_reaching_a_step(self) -> None:
        # Consistent with every other input: an input that reaches a step in any way is not
        # "bound nowhere", and the interpolation rule is the one that fires.
        used = UNBOUND.replace(
            '        echo "$CONFIG" "$GAUGE_REF"',
            '        echo "$CONFIG" "$GAUGE_REF" "${{ inputs.github-token }}"',
        )
        found = problems(used)
        self.assertTrue(mentions(found, "reaches the shell"), found)
        self.assertFalse(mentions(found, "github-token is declared but never bound"), found)


if __name__ == "__main__":
    unittest.main()
