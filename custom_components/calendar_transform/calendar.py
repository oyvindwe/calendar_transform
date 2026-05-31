"""Calendar platform for Calendar Transform."""

from __future__ import annotations

import dataclasses
from datetime import datetime
import re

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.components.calendar.const import DATA_COMPONENT
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import Event, EventStateChangedData, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import CONF_PATTERN, CONF_REPLACEMENT, CONF_SOURCE_ENTITY


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Calendar Transform calendar entity."""
    async_add_entities(
        [
            CalendarTransformEntity(
                entry_id=entry.entry_id,
                name=entry.options[CONF_NAME],
                source_entity_id=entry.options[CONF_SOURCE_ENTITY],
                pattern=entry.options[CONF_PATTERN],
                replacement=entry.options.get(CONF_REPLACEMENT, ""),
            )
        ]
    )


class CalendarTransformEntity(CalendarEntity):
    """Wrap a calendar entity, replacing each event's summary with a regex capture from its description."""

    def __init__(
        self,
        entry_id: str,
        name: str,
        source_entity_id: str,
        pattern: str,
        replacement: str,
    ) -> None:
        """Initialize the entity."""
        self._attr_name = name
        self._attr_unique_id = entry_id
        self._source_entity_id = source_entity_id
        self._pattern = re.compile(pattern, re.MULTILINE)
        self._replacement = replacement or r"\1"

    async def async_added_to_hass(self) -> None:
        """Subscribe to source state changes so our state updates immediately."""
        await super().async_added_to_hass()
        self.async_on_remove(
            async_track_state_change_event(
                self.hass,
                [self._source_entity_id],
                self._handle_source_state_change,
            )
        )

    @callback
    def _handle_source_state_change(
        self, _event: Event[EventStateChangedData]
    ) -> None:
        self.async_write_ha_state()

    def _get_source(self) -> CalendarEntity | None:
        """Return the source CalendarEntity, or None if it isn't available."""
        return self.hass.data[DATA_COMPONENT].get_entity(self._source_entity_id)

    def _transform(self, event: CalendarEvent) -> CalendarEvent:
        """Replace the summary if the regex matches the description."""
        if not event.description:
            return event
        match = self._pattern.search(event.description)
        if match is None:
            return event
        try:
            new_summary = match.expand(self._replacement)
        except re.error:
            return event
        if not new_summary:
            return event
        return dataclasses.replace(event, summary=new_summary)

    @property
    def event(self) -> CalendarEvent | None:
        """Return the current/next event from the source, transformed."""
        source = self._get_source()
        if source is None or source.event is None:
            return None
        return self._transform(source.event)

    @property
    def available(self) -> bool:
        """Mirror the source entity's availability."""
        source = self._get_source()
        return source is not None and source.available

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Return events from the source, with summaries transformed."""
        source = self._get_source()
        if source is None:
            return []
        events = await source.async_get_events(hass, start_date, end_date)
        return [self._transform(event) for event in events]
