"""Tests for the summary transformation logic."""

from datetime import datetime, timezone

from homeassistant.components.calendar import CalendarEvent
import pytest

from custom_components.calendar_transform.calendar import CalendarTransformEntity

DESCRIPTION = (
    "\n Jenter 08 år avd. 02 (runde 3)\n\n"
    " Dikemark J8 Sparkles - Jutul J8 Grønn\n"
    " Dikemark kunstgress 5er A torsdag 01.05.25 18.00 \n\n"
    " www.fotball.no\n"
)


def _make_entity(
    pattern: str = r"(.*)", replacement: str = "", blocklist: str = ""
) -> CalendarTransformEntity:
    return CalendarTransformEntity(
        entry_id="test",
        name="Wrapped",
        source_entity_id="calendar.source",
        pattern=pattern,
        replacement=replacement,
        blocklist=blocklist,
    )


def _event(summary: str, description: str | None) -> CalendarEvent:
    return CalendarEvent(
        start=datetime(2025, 5, 1, 18, 0, tzinfo=timezone.utc),
        end=datetime(2025, 5, 1, 19, 0, tzinfo=timezone.utc),
        summary=summary,
        description=description,
    )


def test_first_capture_group_used_when_replacement_empty() -> None:
    """An empty replacement falls back to the first capture group."""
    entity = _make_entity(r"\n\n\s(.*)\n")
    result = entity._transform(_event("Jenter 08 år avd. 02", DESCRIPTION))
    assert result.summary == "Dikemark J8 Sparkles - Jutul J8 Grønn"


def test_replacement_template_with_backreferences() -> None:
    """Backreferences in the replacement reorder capture groups."""
    entity = _make_entity(r"\n\n\s(.+) - (.+)\n", r"\2 vs \1")
    result = entity._transform(_event("Jenter 08 år avd. 02", DESCRIPTION))
    assert result.summary == "Jutul J8 Grønn vs Dikemark J8 Sparkles"


def test_no_match_keeps_original_summary() -> None:
    """A description that doesn't match leaves the summary untouched."""
    entity = _make_entity(r"NOPE(.*)")
    result = entity._transform(_event("Original", DESCRIPTION))
    assert result.summary == "Original"


def test_missing_description_keeps_original_summary() -> None:
    """An event without a description is returned unchanged."""
    entity = _make_entity(r"(.*)")
    event = _event("Original", None)
    assert entity._transform(event) is event


def test_empty_match_keeps_original_summary() -> None:
    """A match that expands to an empty string keeps the original summary."""
    entity = _make_entity(r"(x*)")
    result = entity._transform(_event("Original", "no x here at start"))
    assert result.summary == "Original"


def test_transform_does_not_mutate_source_event() -> None:
    """The source event is copied, not modified in place."""
    entity = _make_entity(r"\n\n\s(.*)\n")
    event = _event("Jenter 08 år avd. 02", DESCRIPTION)
    entity._transform(event)
    assert event.summary == "Jenter 08 år avd. 02"


@pytest.mark.parametrize("replacement", [r"\9", "\\"])
def test_invalid_replacement_keeps_original_summary(replacement: str) -> None:
    """A replacement that fails to expand falls back to the original summary."""
    entity = _make_entity(r"\n\n\s(.*)\n", replacement)
    result = entity._transform(_event("Original", DESCRIPTION))
    assert result.summary == "Original"


def test_empty_pattern_keeps_original_summary() -> None:
    """With no substitute pattern (filter-only), the summary is left unchanged."""
    entity = _make_entity(pattern="", blocklist=r"nope")
    event = _event("Original", DESCRIPTION)
    assert entity._transform(event) is event


def test_no_blocklist_keeps_all_events() -> None:
    """Without a blocklist, no event is blocked."""
    entity = _make_entity()
    assert entity._is_blocked(_event("Task", "tasks.google.com/task/abc")) is False


def test_blocklist_matches_description() -> None:
    """An event whose description matches the blocklist is blocked."""
    entity = _make_entity(blocklist=r"tasks\.google\.com/task/")
    assert entity._is_blocked(_event("Task", "see tasks.google.com/task/abc")) is True


def test_blocklist_no_match_keeps_event() -> None:
    """An event whose description doesn't match the blocklist is kept."""
    entity = _make_entity(blocklist=r"tasks\.google\.com/task/")
    assert entity._is_blocked(_event("Match", DESCRIPTION)) is False


def test_blocklist_ignores_events_without_description() -> None:
    """An event without a description is never blocked."""
    entity = _make_entity(blocklist=r".*")
    assert entity._is_blocked(_event("No description", None)) is False
