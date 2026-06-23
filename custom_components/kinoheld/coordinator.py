"""DataUpdateCoordinator for Kinoheld."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import KinoheldApiError, KinoheldClient
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class KinoheldCoordinator(DataUpdateCoordinator):
    """Fetch program data from Kinoheld and cache it."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: KinoheldClient,
        cinema_id: str,
        cinema_name: str,
        scan_interval: int,
    ) -> None:
        self.client = client
        self.cinema_id = cinema_id
        self.cinema_name = cinema_name

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{cinema_id}",
            update_interval=timedelta(minutes=scan_interval),
        )

    async def _async_update_data(self) -> dict:
        """Fetch fresh program data."""
        try:
            movies = await self.client.get_program(cinema_ids=[self.cinema_id])
        except KinoheldApiError as err:
            raise UpdateFailed(f"Error fetching Kinoheld data: {err}") from err

        # Flatten into a clean list of dicts for easy sensor consumption
        result: list[dict] = []
        for entry in movies:
            movie = entry.get("movie", {})
            shows = entry.get("shows", [])
            genres = [g["name"] for g in movie.get("genres", [])]
            next_show = shows[0]["beginning"] if shows else None
            result.append(
                {
                    "id": movie.get("id"),
                    "title": movie.get("title"),
                    "duration": movie.get("duration"),
                    "released": movie.get("released"),
                    "genres": genres,
                    "url": f"https://www.kinoheld.de/kino/{self.cinema_id}/film/{movie.get('urlSlug', '')}",
                    "poster_url": (movie.get("posterImage") or {}).get("url"),
                    "thumbnail_url": (movie.get("thumbnailImage") or {}).get("url"),
                    "next_show": next_show,
                    "show_count": len(shows),
                    "shows": [
                        {
                            "id": s.get("id"),
                            "beginning": s.get("beginning"),
                            "language": (s.get("flags") or {}).get("languageFlag"),
                            "technology": (s.get("flags") or {}).get("technologyFlag"),
                        }
                        for s in shows
                    ],
                }
            )

        _LOGGER.debug(
            "Kinoheld [%s]: fetched %d movies", self.cinema_name, len(result)
        )
        return {"movies": result, "cinema_name": self.cinema_name, "cinema_id": self.cinema_id}
