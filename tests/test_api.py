"""Tests for the Kinoheld API client."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.kinoheld.api import KinoheldApiError, KinoheldClient


MOCK_CINEMA = {
    "__typename": "Cinema",
    "id": "1001",
    "name": "Cineplex Weiden",
    "urlSlug": "cineplex-weiden",
    "street": "Musterstraße 1",
    "isOpenAir": False,
    "isDriveIn": False,
    "isStationary": True,
    "postcode": {"postcode": "92637"},
    "city": {"id": "500", "urlSlug": "weiden", "name": "Weiden"},
    "thumbnailImage": None,
}

MOCK_PROGRAM = {
    "programByMovie": {
        "edges": [
            {
                "node": {
                    "movie": {
                        "id": "m1",
                        "title": "Test Film",
                        "urlSlug": "test-film",
                        "duration": 120,
                        "released": "2025-06-01",
                        "genres": [{"id": "g1", "name": "Action", "urlSlug": "action"}],
                        "thumbnailImage": None,
                        "posterImage": None,
                    },
                    "shows": [
                        {
                            "id": "s1",
                            "beginning": "2025-07-01T19:30:00",
                            "flags": {"languageFlag": "de", "technologyFlag": "2D"},
                        }
                    ],
                }
            }
        ],
        "pageInfo": {"hasNextPage": False, "endCursor": None},
    }
}


@pytest.mark.asyncio
async def test_search_cinemas_returns_results():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = AsyncMock(return_value={"data": {"search": [MOCK_CINEMA]}})
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=False)

    mock_session = MagicMock()
    mock_session.post = MagicMock(return_value=mock_response)

    client = KinoheldClient(mock_session)
    results = await client.search_cinemas("Weiden")

    assert len(results) == 1
    assert results[0]["name"] == "Cineplex Weiden"
    assert results[0]["id"] == "1001"


@pytest.mark.asyncio
async def test_search_cinemas_filters_non_cinema():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = AsyncMock(
        return_value={
            "data": {
                "search": [
                    MOCK_CINEMA,
                    {"__typename": "City", "id": "999", "name": "Weiden"},
                ]
            }
        }
    )
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=False)

    mock_session = MagicMock()
    mock_session.post = MagicMock(return_value=mock_response)

    client = KinoheldClient(mock_session)
    results = await client.search_cinemas("Weiden")

    assert len(results) == 1  # City filtered out
    assert results[0]["__typename"] == "Cinema"


@pytest.mark.asyncio
async def test_get_program_returns_movies():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = AsyncMock(return_value={"data": MOCK_PROGRAM})
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=False)

    mock_session = MagicMock()
    mock_session.post = MagicMock(return_value=mock_response)

    client = KinoheldClient(mock_session)
    movies = await client.get_program(["1001"])

    assert len(movies) == 1
    assert movies[0]["movie"]["title"] == "Test Film"


@pytest.mark.asyncio
async def test_api_error_on_graphql_error():
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json = AsyncMock(
        return_value={"errors": [{"message": "Cinema not found"}]}
    )
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=False)

    mock_session = MagicMock()
    mock_session.post = MagicMock(return_value=mock_response)

    client = KinoheldClient(mock_session)
    with pytest.raises(KinoheldApiError, match="Cinema not found"):
        await client.search_cinemas("Weiden")
