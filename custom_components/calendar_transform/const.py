"""Constants for the Calendar Transform integration."""

from homeassistant.const import Platform

DOMAIN = "calendar_transform"

PLATFORMS = [Platform.CALENDAR]

CONF_SOURCE_ENTITY = "source_entity"
CONF_PATTERN = "pattern"
CONF_REPLACEMENT = "replacement"
