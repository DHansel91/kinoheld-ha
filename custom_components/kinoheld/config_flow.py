"""Config flow for Kinoheld integration."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import KinoheldApiError, KinoheldClient
from .const import (
    CONF_CINEMA_CITY,
    CONF_CINEMA_ID,
    CONF_CINEMA_NAME,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class KinoheldConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Kinoheld."""

    VERSION = 1

    def __init__(self) -> None:
        self._cinemas: list[dict] = []
        self._search_query: str = ""

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Step 1: Search for a cinema by name or city."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._search_query = user_input["search_query"].strip()
            session = async_get_clientsession(self.hass)
            client = KinoheldClient(session)

            try:
                results = await client.search_cinemas(self._search_query)
            except KinoheldApiError:
                errors["base"] = "cannot_connect"
            else:
                if not results:
                    errors["search_query"] = "no_results"
                else:
                    self._cinemas = results
                    return await self.async_step_select_cinema()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required("search_query", default=self._search_query): str}
            ),
            errors=errors,
            description_placeholders={"example": "Weiden"},
        )

    async def async_step_select_cinema(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        """Step 2: Let the user pick from the search results."""
        errors: dict[str, str] = {}

        cinema_options = {
            c["id"]: f"{c['name']} – {c.get('city', {}).get('name', '')} ({c.get('postcode', {}).get('postcode', '')})"
            for c in self._cinemas
        }

        if user_input is not None:
            cinema_id = user_input["cinema_id"]
            cinema = next((c for c in self._cinemas if c["id"] == cinema_id), None)
            if cinema is None:
                errors["cinema_id"] = "invalid_cinema"
            else:
                await self.async_set_unique_id(f"kinoheld_{cinema_id}")
                self._abort_if_unique_id_configured()

                return await self.async_step_options(
                    prefill={
                        CONF_CINEMA_ID: cinema_id,
                        CONF_CINEMA_NAME: cinema["name"],
                        CONF_CINEMA_CITY: cinema.get("city", {}).get("name", ""),
                    }
                )

        return self.async_show_form(
            step_id="select_cinema",
            data_schema=vol.Schema(
                {vol.Required("cinema_id"): vol.In(cinema_options)}
            ),
            errors=errors,
        )

    async def async_step_options(
        self,
        user_input: dict[str, Any] | None = None,
        prefill: dict[str, Any] | None = None,
    ) -> config_entries.FlowResult:
        """Step 3: Scan interval."""
        if user_input is not None and prefill is None:
            # Coming from re-submission
            return self.async_create_entry(
                title=user_input[CONF_CINEMA_NAME],
                data={
                    CONF_CINEMA_ID: user_input[CONF_CINEMA_ID],
                    CONF_CINEMA_NAME: user_input[CONF_CINEMA_NAME],
                    CONF_CINEMA_CITY: user_input.get(CONF_CINEMA_CITY, ""),
                    CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
                },
            )

        if prefill:
            # Store prefill, show form
            self._prefill = prefill
            return self.async_show_form(
                step_id="options",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_CINEMA_ID, default=prefill[CONF_CINEMA_ID]): str,
                        vol.Required(CONF_CINEMA_NAME, default=prefill[CONF_CINEMA_NAME]): str,
                        vol.Optional(CONF_CINEMA_CITY, default=prefill[CONF_CINEMA_CITY]): str,
                        vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
                            int, vol.Range(min=15, max=1440)
                        ),
                    }
                ),
            )

        # Submitted from form
        return self.async_create_entry(
            title=user_input[CONF_CINEMA_NAME],
            data={
                CONF_CINEMA_ID: user_input[CONF_CINEMA_ID],
                CONF_CINEMA_NAME: user_input[CONF_CINEMA_NAME],
                CONF_CINEMA_CITY: user_input.get(CONF_CINEMA_CITY, ""),
                CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
            },
        )

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> "KinoheldOptionsFlow":
        return KinoheldOptionsFlow(config_entry)


class KinoheldOptionsFlow(config_entries.OptionsFlow):
    """Options flow to update scan interval."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SCAN_INTERVAL,
                        default=self.config_entry.data.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                    ): vol.All(int, vol.Range(min=15, max=1440)),
                }
            ),
        )
