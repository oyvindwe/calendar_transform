"""Config flow for the Calendar Transform integration."""

from __future__ import annotations

from collections.abc import Mapping
import re
from typing import Any

import voluptuous as vol

from homeassistant.components.calendar import DOMAIN as CALENDAR_DOMAIN
from homeassistant.const import CONF_NAME
from homeassistant.helpers import selector
from homeassistant.helpers.schema_config_entry_flow import (
    SchemaCommonFlowHandler,
    SchemaConfigFlowHandler,
    SchemaFlowError,
    SchemaFlowFormStep,
)

from .const import (
    CONF_BLOCKLIST,
    CONF_PATTERN,
    CONF_REPLACEMENT,
    CONF_SOURCE_ENTITY,
    DOMAIN,
)

_BACKREF_RE = re.compile(r"\\(\d+)")


async def _validate_pattern(
    handler: SchemaCommonFlowHandler, user_input: dict[str, Any]
) -> dict[str, Any]:
    """Validate the substitute and filter patterns and the replacement template."""
    pattern = user_input.get(CONF_PATTERN, "")
    blocklist = user_input.get(CONF_BLOCKLIST, "")
    if not pattern and not blocklist:
        raise SchemaFlowError("pattern_or_blocklist_required")
    if pattern:
        try:
            compiled = re.compile(pattern, re.MULTILINE)
        except re.error as err:
            raise SchemaFlowError("invalid_regex") from err
        if compiled.groups < 1:
            raise SchemaFlowError("no_capture_group")
        replacement = user_input.get(CONF_REPLACEMENT, "")
        if replacement:
            backrefs = [int(b) for b in _BACKREF_RE.findall(replacement)]
            if backrefs and max(backrefs) > compiled.groups:
                raise SchemaFlowError("invalid_backreference")
    if blocklist:
        try:
            re.compile(blocklist, re.MULTILINE)
        except re.error as err:
            raise SchemaFlowError("invalid_blocklist") from err
    return user_input


OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_SOURCE_ENTITY): selector.EntitySelector(
            selector.EntitySelectorConfig(domain=CALENDAR_DOMAIN)
        ),
        vol.Optional(CONF_PATTERN, default=""): selector.TextSelector(
            selector.TextSelectorConfig(multiline=True)
        ),
        vol.Optional(CONF_REPLACEMENT, default=""): selector.TextSelector(),
        vol.Optional(CONF_BLOCKLIST, default=""): selector.TextSelector(
            selector.TextSelectorConfig(multiline=True)
        ),
    }
)

CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): selector.TextSelector(),
    }
).extend(OPTIONS_SCHEMA.schema)

CONFIG_FLOW = {
    "user": SchemaFlowFormStep(CONFIG_SCHEMA, validate_user_input=_validate_pattern),
}

OPTIONS_FLOW = {
    "init": SchemaFlowFormStep(OPTIONS_SCHEMA, validate_user_input=_validate_pattern),
}


class CalendarTransformConfigFlow(SchemaConfigFlowHandler, domain=DOMAIN):
    """Handle a config or options flow for Calendar Transform."""

    config_flow = CONFIG_FLOW
    options_flow = OPTIONS_FLOW
    options_flow_reloads = True

    def async_config_entry_title(self, options: Mapping[str, Any]) -> str:
        """Return the title for the config entry."""
        return str(options[CONF_NAME])
