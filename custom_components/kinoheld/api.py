"""Kinoheld GraphQL API client."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)

GRAPHQL_URL = "https://next-live.kinoheld.de/graphql"

QUERY_SEARCH_CINEMA = """
query FetchSearchForAutoSuggest($query: String, $limit: Int! = 25, $types: [SearchTypeEnum!]) {
  search(query: $query, limit: $limit, types: $types) {
    __typename
    ... on Cinema {
      id
      name
      urlSlug
      street
      isOpenAir
      isDriveIn
      isStationary
      postcode { postcode }
      city { id urlSlug name }
      thumbnailImage { id url width height }
    }
  }
}
"""

QUERY_PROGRAM_FILTERS = """
query FetchProgramFilters($cinemaIds: [ID!]!, $showGroups: [String!], $filters: [String!]) {
  programByMovie(cinemaIds: $cinemaIds, showGroups: $showGroups, first: 1) {
    filterOptions(filters: $filters) {
      key
      label
      values { key label }
    }
  }
}
"""

QUERY_PROGRAM_BY_MOVIE = """
query FetchProgramByMovie(
  $cinemaIds: [ID!]!,
  $dates: [String!],
  $languageFlags: [String!],
  $technologyFlags: [String!],
  $first: Int! = 50,
  $page: Int
) {
  programByMovie(
    cinemaIds: $cinemaIds,
    dates: $dates,
    languageFlags: $languageFlags,
    technologyFlags: $technologyFlags,
    first: $first,
    page: $page
  ) {
    data {
      movie {
        id
        title
        urlSlug
        duration
        released
        genres { id name urlSlug }
        thumbnailImage { id url width height }
        posterImage { id url width height }
      }
      shows {
        id
        beginning
        flags { languageFlag technologyFlag }
      }
    }
    paginatorInfo {
      hasMorePages
      currentPage
      lastPage
    }
  }
}
"""

QUERY_SHOWS_BY_MOVIE = """
query FetchShowsByMovie(
  $cinemaIds: [ID!]!,
  $movieId: ID!,
  $date: String
) {
  showsByMovie(cinemaIds: $cinemaIds, movieId: $movieId, date: $date) {
    id
    beginning
    end
    flags { languageFlag technologyFlag }
    cinema { id name }
  }
}
"""


class KinoheldApiError(Exception):
    """Raised when the Kinoheld API returns an error."""


class KinoheldClient:
    """Async GraphQL client for Kinoheld."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session

    async def _post(self, query: str, variables: dict[str, Any], operation: str) -> dict[str, Any]:
        payload = {"query": query, "variables": variables, "operationName": operation}
        try:
            async with self._session.post(
                GRAPHQL_URL,
                json=payload,
                headers={"Content-Type": "application/json", "Accept": "application/json"},
                timeout=aiohttp.ClientTimeout(total=20),
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
        except aiohttp.ClientResponseError as err:
            raise KinoheldApiError(f"HTTP {err.status}: {err.message}") from err
        except aiohttp.ClientError as err:
            raise KinoheldApiError(f"Connection error: {err}") from err

        if "errors" in data:
            msg = "; ".join(e.get("message", str(e)) for e in data["errors"])
            raise KinoheldApiError(f"GraphQL error: {msg}")

        return data.get("data", {})

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    async def search_cinemas(self, query: str, limit: int = 25) -> list[dict[str, Any]]:
        """Return Cinema results matching *query*."""
        data = await self._post(
            QUERY_SEARCH_CINEMA,
            {"query": query, "limit": limit, "types": ["CINEMA"]},
            "FetchSearchForAutoSuggest",
        )
        results = data.get("search", [])
        return [r for r in results if r.get("__typename") == "Cinema"]

    async def get_program_filters(self, cinema_ids: list[str]) -> list[dict[str, Any]]:
        """Return available filter options for the given cinemas."""
        data = await self._post(
            QUERY_PROGRAM_FILTERS,
            {
                "cinemaIds": cinema_ids,
                "filters": [
                    "search",
                    "dates",
                    "languageFlags",
                    "technologyFlags",
                    "showGroups",
                    "contentRatings",
                    "genres",
                    "eventFlags",
                    "miscellaneousFlags",
                ],
            },
            "FetchProgramFilters",
        )
        return data.get("programByMovie", {}).get("filterOptions", [])

    async def get_program(
        self,
        cinema_ids: list[str],
        show_dates: list[str] | None = None,
        language_flags: list[str] | None = None,
        technology_flags: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Return all movies playing at the given cinemas (page-based pagination)."""
        variables: dict[str, Any] = {"cinemaIds": cinema_ids, "first": 50}
        if show_dates:
            variables["dates"] = show_dates
        if language_flags:
            variables["languageFlags"] = language_flags
        if technology_flags:
            variables["technologyFlags"] = technology_flags

        movies: list[dict[str, Any]] = []
        page = 1

        while True:
            variables["page"] = page
            data = await self._post(QUERY_PROGRAM_BY_MOVIE, variables, "FetchProgramByMovie")
            program = data.get("programByMovie", {})
            items = program.get("data", [])
            movies.extend(items)

            paginator = program.get("paginatorInfo", {})
            if not paginator.get("hasMorePages") or page >= paginator.get("lastPage", 1):
                break
            page += 1

        return movies
