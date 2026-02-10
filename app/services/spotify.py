"""Spotify API service for fetching user data"""

import httpx


async def get_top_artists(
    access_token: str, time_range: str = "medium_term", limit: int = 50
):
    """Fetch user's top artists from Spotify API"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.spotify.com/v1/me/top/artists",
                headers={"Authorization": f"Bearer {access_token}"},
                params={"time_range": time_range, "limit": limit},
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        raise Exception(f"Failed to fetch top artists: {str(e)}")


async def get_top_tracks(
    access_token: str, time_range: str = "medium_term", limit: int = 50
):
    """Fetch user's top tracks from Spotify API"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.spotify.com/v1/me/top/tracks",
                headers={"Authorization": f"Bearer {access_token}"},
                params={"time_range": time_range, "limit": limit},
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        raise Exception(f"Failed to fetch top tracks: {str(e)}")


async def get_playlists(access_token: str, limit: int = 50):
    """Fetch user's playlists from Spotify API"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.spotify.com/v1/me/playlists",
                headers={"Authorization": f"Bearer {access_token}"},
                params={"limit": limit},
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        raise Exception(f"Failed to fetch playlists: {str(e)}")
