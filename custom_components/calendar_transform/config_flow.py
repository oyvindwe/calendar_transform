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

from .const import CONF_PATTERN, CONF_REPLACEMENT, CONF_SOURCE_ENTITY, DOMAIN

_BACKREF_RE = re.compile(r"\\(\d+)")


async def _validate_pattern(
    handler: SchemaCommonFlowHandler, user_input: dict[str, Any]
) -> dict[str, Any]:
    """Validate the regex and replacement template."""
    try:
        compiled = re.compile(user_input[CONF_PATTERN], re.MULTILINE)
    except re.error as err:
        raise SchemaFlowError("invalid_regex") from err
    if compiled.groups < 1:
        raise SchemaFlowError("no_capture_group")
    replacement = user_input.get(CONF_REPLACEMENT, "")
    if replacement:
        backrefs = [int(b) for b in _BACKREF_RE.findall(replacement)]
        if backrefs and max(backrefs) > compiled.groups:
            raise SchemaFlowError("invalid_backreference")
    return user_input


OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_SOURCE_ENTITY): selector.EntitySelector(
            selector.EntitySelectorConfig(domain=CALENDAR_DOMAIN)
        ),
        vol.Required(CONF_PATTERN): selector.TextSelector(
            selector.TextSelectorConfig(multiline=True)
        ),
        vol.Optional(CONF_REPLACEMENT, default=""): selector.TextSelector(),
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
