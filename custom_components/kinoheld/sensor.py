"""Sensor platform for Kinoheld."""
from __future__ import annotations

import logging
from datetime import datetime

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_CINEMA_ID,
    ATTR_CINEMA_NAME,
    ATTR_LAST_UPDATED,
    ATTR_MOVIE_COUNT,
    ATTR_MOVIES,
    CONF_CINEMA_ID,
    CONF_CINEMA_NAME,
    DOMAIN,
    UPDATE_COORDINATOR,
)
from .coordinator import KinoheldCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Kinoheld sensors."""
    coordinator: KinoheldCoordinator = hass.data[DOMAIN][entry.entry_id][UPDATE_COORDINATOR]
    async_add_entities(
        [
            KinoheldProgramSensor(coordinator, entry),
            KinoheldNowPlayingSensor(coordinator, entry),
        ]
    )


class _KinoheldBaseSensor(CoordinatorEntity[KinoheldCoordinator], SensorEntity):
    """Base class for Kinoheld sensors."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: KinoheldCoordinator,
        entry: ConfigEntry,
        key: str,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        cinema_id = entry.data[CONF_CINEMA_ID]
        self._attr_unique_id = f"kinoheld_{cinema_id}_{key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, cinema_id)},
            "name": entry.data[CONF_CINEMA_NAME],
            "manufacturer": "Kinoheld",
            "model": "Cinema",
            "configuration_url": f"https://www.kinoheld.de/kino-{coordinator.cinema_id}",
        }

    @property
    def _movies(self) -> list[dict]:
        return (self.coordinator.data or {}).get("movies", [])


class KinoheldProgramSensor(_KinoheldBaseSensor):
    """Sensor that exposes the full cinema program."""

    _attr_icon = "mdi:movie-open"

    def __init__(self, coordinator: KinoheldCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "program")
        self._attr_name = "Programm"

    @property
    def native_value(self) -> int:
        """State = number of movies currently showing."""
        return len(self._movies)

    @property
    def native_unit_of_measurement(self) -> str:
        return "Filme"

    @property
    def extra_state_attributes(self) -> dict:
        movies = self._movies
        return {
            ATTR_CINEMA_NAME: self.coordinator.cinema_name,
            ATTR_CINEMA_ID: self.coordinator.cinema_id,
            ATTR_MOVIE_COUNT: len(movies),
            ATTR_MOVIES: movies,
            ATTR_LAST_UPDATED: datetime.now().isoformat(),
        }


class KinoheldNowPlayingSensor(_KinoheldBaseSensor):
    """Sensor showing the next upcoming movie (earliest next_show)."""

    _attr_icon = "mdi:movie-play"

    def __init__(self, coordinator: KinoheldCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "now_playing")
        self._attr_name = "Nächste Vorstellung"

    @property
    def _next_movie(self) -> dict | None:
        movies_with_shows = [m for m in self._movies if m.get("next_show")]
        if not movies_with_shows:
            return None
        return min(movies_with_shows, key=lambda m: m["next_show"])

    @property
    def native_value(self) -> str | None:
        movie = self._next_movie
        return movie["title"] if movie else None

    @property
    def extra_state_attributes(self) -> dict:
        movie = self._next_movie
        if not movie:
            return {}
        return {
            "title": movie.get("title"),
            "next_show": movie.get("next_show"),
            "duration": movie.get("duration"),
            "genres": movie.get("genres", []),
            "url": movie.get("url"),
            "poster_url": movie.get("poster_url"),
            "show_count": movie.get("show_count", 0),
        }
