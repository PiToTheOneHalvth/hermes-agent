"""Terminal showcase colors for reasoning text (user spec 2026-10-05).

Main text renders in the Homebrew-terminal green, order marks ("1." "2.")
in orange, § log marks and #PR numbers in white. Unit tests for the CLI
colorizer in hermes_cli/cli_stream_mixin.py.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from hermes_cli.cli_stream_mixin import (  # noqa: E402
    _THINKING_GREEN,
    _THINKING_ORANGE,
    _THINKING_PARTIAL_TAIL_RE,
    _THINKING_WHITE,
    _thinking_line,
)

RST = "\033[0m"


def test_main_text_is_green():
    assert _thinking_line("hello") == f"{_THINKING_GREEN}hello{RST}"


def test_log_mark_is_white_and_resets_to_green():
    assert _thinking_line("see §[2026-10-02] log") == (
        f"{_THINKING_GREEN}see {_THINKING_WHITE}§[2026-10-02]{_THINKING_GREEN} log{RST}"
    )


def test_spaced_log_mark_is_white():
    # The green base wrapper always opens the line, even when a token starts it.
    assert _thinking_line("§ [2026-10-02] spaced") == (
        f"{_THINKING_GREEN}{_THINKING_WHITE}§ [2026-10-02]{_THINKING_GREEN} spaced{RST}"
    )


def test_pr_number_is_white():
    assert _thinking_line("PR #123456 merged") == (
        f"{_THINKING_GREEN}PR {_THINKING_WHITE}#123456{_THINKING_GREEN} merged{RST}"
    )


def test_short_hash_is_not_a_pr_number():
    assert _thinking_line("hash #12345 stays") == f"{_THINKING_GREEN}hash #12345 stays{RST}"


def test_order_marks_are_orange():
    assert _thinking_line("do 1. one then 2. two") == (
        f"{_THINKING_GREEN}do {_THINKING_ORANGE}1.{_THINKING_GREEN} one then "
        f"{_THINKING_ORANGE}2.{_THINKING_GREEN} two{RST}"
    )


def test_decimals_and_versions_stay_green():
    line = _thinking_line("pi 3.14, v1.0.1, 2.5 hours")
    assert _THINKING_ORANGE not in line
    assert line == f"{_THINKING_GREEN}pi 3.14, v1.0.1, 2.5 hours{RST}"


def test_section_mark_containing_pr_number_is_one_white_span():
    assert _thinking_line("x §[#123456] y") == (
        f"{_THINKING_GREEN}x {_THINKING_WHITE}§[#123456]{_THINKING_GREEN} y{RST}"
    )


@pytest.mark.parametrize(
    ("buffer", "expected"),
    [
        # Incomplete tail tokens must be held so they can be colored in one print.
        ("open §[2026-10", "§[2026-10"),
        ("PR #12345", "#12345"),
        ("step 1.", "1."),
        # Complete tokens, decimals, and plain tails are not partials.
        ("§[2026-10-02]", None),
        ("PR #123456", None),
        ("value 3.1", None),
        ("plain tail", None),
    ],
)
def test_partial_tail_detection(buffer, expected):
    match = _THINKING_PARTIAL_TAIL_RE.search(buffer)
    assert (match.group(0) if match else None) == expected


def test_partial_tail_cut_position_is_before_the_token():
    match = _THINKING_PARTIAL_TAIL_RE.search("first §[2026-10")
    assert match is not None
    assert match.start() == len("first ")


def test_empty_line_stays_wrapped():
    assert _thinking_line("") == f"{_THINKING_GREEN}{RST}"
