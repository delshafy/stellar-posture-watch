#!/usr/bin/env python3
"""Tests for the issue-label length limit in `scripts/validate_inputs.py` (#70).

`check_text_input()` applied one constant to two different fields: the 256 characters a
GitHub issue title may carry, and the label GitHub caps at 50. A 60 character label
therefore cleared the preflight, bought a Go build, and came back as a 422 from the issue
API minutes into a schedule, in a message that did not say the label was too long. These
cases sit on both sides of both boundaries, and check that the title rule did not move.

Counting is by character, not byte, and nothing is trimmed: the value the operator wrote is
the value the API sees, so a trailing space belongs to the length.

Run: python3 -m unittest discover -s tests -t tests
"""

from __future__ import annotations

import unittest

from test_validate_inputs import Harness


class LabelLimit(Harness):
    def run_label(self, value: str) -> tuple[int, str, str]:
        return self.run_cli(issue_label=value)

    def run_title(self, value: str) -> tuple[int, str, str]:
        return self.run_cli(title=value)

    def test_a_fifty_character_label_passes(self) -> None:
        code, _, err = self.run_label("l" * 50)
        self.assertEqual(code, 0, err)

    def test_a_fifty_one_character_label_is_refused_by_name_and_length(self) -> None:
        code, _, err = self.run_label("l" * 51)
        self.assertEqual(code, 2)
        self.assertEqual(
            err, "validate_inputs: refused\n  - issue-label is 51 characters, over the 50 limit\n"
        )

    def test_the_title_keeps_its_own_limit(self) -> None:
        code, _, err = self.run_title("t" * 256)
        self.assertEqual(code, 0, err)
        code, _, err = self.run_title("t" * 257)
        self.assertEqual(code, 2)
        self.assertIn("title is 257 characters, over the 256 limit", err)

    def test_both_limits_are_reported_together(self) -> None:
        code, _, err = self.run_cli(issue_label="l" * 51, title="t" * 257)
        self.assertEqual(code, 2)
        self.assertIn("issue-label is 51 characters, over the 50 limit", err)
        self.assertIn("title is 257 characters, over the 256 limit", err)

    def test_the_default_label_is_far_inside_the_limit(self) -> None:
        # action.yml ships `account-posture`; the narrower rule must not refuse the
        # configuration every scheduled run already uses.
        code, _, err = self.run_cli()
        self.assertEqual(code, 0, err)

    def test_the_empty_and_control_character_messages_are_unchanged(self) -> None:
        for name, hostile in (
            ("issue_label", "account\nposture"),
            ("title", "Account\nposture watch"),
        ):
            with self.subTest(name=name):
                code, _, err = self.run_cli(**{name: ""})
                self.assertEqual(code, 2)
                self.assertIn(f"{name.replace('_', '-')} must not be empty", err)
                code, _, err = self.run_cli(**{name: hostile})
                self.assertEqual(code, 2)
                self.assertIn("carries a control character or a line break", err)

    def test_the_label_limit_counts_characters_not_bytes(self) -> None:
        # 50 of these are 150 bytes in UTF-8; the limit is the one GitHub applies to the
        # name it stores, which is characters.
        code, _, err = self.run_label("é" * 50)
        self.assertEqual(code, 0, err)
        code, _, err = self.run_label("é" * 51)
        self.assertEqual(code, 2)
        self.assertIn("issue-label is 51 characters, over the 50 limit", err)

    def test_the_label_is_not_trimmed_before_counting(self) -> None:
        code, _, err = self.run_label("l" * 49 + " ")
        self.assertEqual(code, 0, err)
        code, _, err = self.run_label("l" * 50 + " ")
        self.assertEqual(code, 2)
        self.assertIn("issue-label is 51 characters, over the 50 limit", err)


if __name__ == "__main__":
    unittest.main()
