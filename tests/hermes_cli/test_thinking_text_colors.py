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


def test_version_tail_with_sentence_period_stays_green():
    # "7." in "python-3.14.7." is a version digit + period, not an order mark.
    line = _thinking_line("runtime is python-3.14.7. Done.")
    assert _THINKING_ORANGE not in line
    assert line == f"{_THINKING_GREEN}runtime is python-3.14.7. Done.{RST}"


def test_letter_adjacent_number_mark_stays_green():
    line = _thinking_line("file x1. step and a17. step")
    assert _THINKING_ORANGE not in line
    assert line == f"{_THINKING_GREEN}file x1. step and a17. step{RST}"


def test_section_mark_containing_pr_number_is_one_white_span():
    assert _thinking_line("x §[#123456] y") == (
        f"{_THINKING_GREEN}x {_THINKING_WHITE}§[#123456]{_THINKING_GREEN} y{RST}"
    )


def test_website_url_is_white():
    assert _thinking_line("see https://example.com/x for more") == (
        f"{_THINKING_GREEN}see {_THINKING_WHITE}https://example.com/x{_THINKING_GREEN} for more{RST}"
    )


def test_website_url_trailing_punctuation_stays_green():
    assert _thinking_line("(https://example.com/a).") == (
        f"{_THINKING_GREEN}({_THINKING_WHITE}https://example.com/a{_THINKING_GREEN}).{RST}"
    )


def test_website_url_with_pr_fragment_is_one_white_span():
    assert _thinking_line("x https://github.com/a/issues/133125#top y") == (
        f"{_THINKING_GREEN}x {_THINKING_WHITE}https://github.com/a/issues/133125#top"
        f"{_THINKING_GREEN} y{RST}"
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
        ("at https://example.com/a", "https://example.com/a"),
        ("done https://example.com/a ", None),
        ("python-3.14.7.", None),
        ("step 1.", "1."),
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


# ---- Config knob: display.thinking_colors overrides the spec palette ----


def test_thinking_hex_to_ansi_valid_and_invalid():
    from hermes_cli.cli_stream_mixin import _thinking_hex_to_ansi

    assert _thinking_hex_to_ansi("#FF0000") == "\033[38;2;255;0;0m"
    assert _thinking_hex_to_ansi(" #a1B2c3 ") == "\033[38;2;161;178;195m"
    assert _thinking_hex_to_ansi("#GGGGGG") is None
    assert _thinking_hex_to_ansi("red") is None
    assert _thinking_hex_to_ansi("#FFF") is None
    assert _thinking_hex_to_ansi("") is None
    assert _thinking_hex_to_ansi(None) is None


def test_all_five_classes_resolve_from_config(monkeypatch):
    import hermes_cli.cli_stream_mixin as csm

    monkeypatch.setattr(csm, "_thinking_config_overrides", lambda: {
        "main": "#FF0000", "order": "#00FF00", "log": "#0000FF",
        "pr": "#ABCDEF", "url": "#123456",
    })
    MAIN, ORDER, LOG, PR, URL = (
        "\033[38;2;255;0;0m", "\033[38;2;0;255;0m", "\033[38;2;0;0;255m",
        "\033[38;2;171;205;239m", "\033[38;2;18;52;86m",
    )
    line = _thinking_line("see §[2026-10-02], PR #123456, https://a.com/x and 1. item")
    assert line == (
        f"{MAIN}see {LOG}§[2026-10-02]{MAIN}, PR {PR}#123456{MAIN}, "
        f"{URL}https://a.com/x{MAIN} and {ORDER}1.{MAIN} item{RST}"
    )


def test_partial_config_keeps_defaults_for_missing_keys(monkeypatch):
    import hermes_cli.cli_stream_mixin as csm

    monkeypatch.setattr(csm, "_thinking_config_overrides", lambda: {"main": "#FF0000"})
    assert _thinking_line("go 1. then §[2026-10-02]") == (
        f"\033[38;2;255;0;0mgo {_THINKING_ORANGE}1.\033[38;2;255;0;0m then "
        f"{_THINKING_WHITE}§[2026-10-02]\033[38;2;255;0;0m{RST}"
    )


def test_invalid_config_values_fall_back_to_defaults(monkeypatch):
    import hermes_cli.cli_stream_mixin as csm

    monkeypatch.setattr(csm, "_thinking_config_overrides",
                        lambda: {"main": "green", "order": "#12", "log": 42})
    assert _thinking_line("1. §[2026-10-02]") == (
        f"{_THINKING_GREEN}{_THINKING_ORANGE}1.{_THINKING_GREEN} "
        f"{_THINKING_WHITE}§[2026-10-02]{_THINKING_GREEN}{RST}"
    )


def test_unreachable_config_falls_back_to_defaults(monkeypatch):
    import hermes_cli.cli_stream_mixin as csm

    def _boom():
        raise RuntimeError("no cli module here")

    monkeypatch.setattr(csm, "_thinking_config_overrides", _boom)
    assert _thinking_line("plain") == f"{_THINKING_GREEN}plain{RST}"
