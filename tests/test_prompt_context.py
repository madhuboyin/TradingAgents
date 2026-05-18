from tradingagents.agents.utils.prompt_context import (
    build_analyst_brief,
    tail_text,
    truncate_text,
)


def test_truncate_text_keeps_short_values():
    assert truncate_text("short", 20) == "short"


def test_truncate_text_adds_suffix():
    result = truncate_text("abcdefghij", 8, suffix="...")
    assert result == "abcde..."


def test_tail_text_keeps_recent_context():
    result = tail_text("1234567890", 4)
    assert result.endswith("7890")
    assert result.startswith("... (recent context only) ...")


def test_build_analyst_brief_skips_empty_sections():
    brief = build_analyst_brief(
        [
            ("Market Analysis", "Momentum improving."),
            ("News Analysis", ""),
        ],
        max_chars_per_section=50,
    )
    assert "## Market Analysis" in brief
    assert "Momentum improving." in brief
    assert "## News Analysis" not in brief
