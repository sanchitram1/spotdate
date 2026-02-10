import json
import os
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse

from app.services.frontend import (
    get_callback_page,
    get_dashboard_page,
    get_login_page,
)

load_dotenv()

app = FastAPI()

# Spotify credentials
CLIENT_ID = os.getenv("REACT_APP_SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("REACT_APP_REDIRECT_URI")

SCOPES = [
    "user-read-private",
    "user-read-email",
    "user-top-read",
    "user-library-read",
    "playlist-read-private",
    "playlist-read-collaborative",
    "user-follow-read",
]

# Store tokens in memory (use database in production)
user_tokens = {}

# Data directory for saving fetched data
DATA_DIR = Path("fetched_data")
DATA_DIR.mkdir(exist_ok=True)


# ==================== AUTHENTICATION ROUTES ====================


@app.get("/api/auth/authorize")
async def authorize():
    """Generate Spotify authorization URL"""
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": " ".join(SCOPES),
    }
    auth_url = f"https://accounts.spotify.com/authorize?{urlencode(params)}"
    return {"auth_url": auth_url}


@app.post("/api/auth/callback")
async def callback(code: str = Form(...)):
    """Exchange authorization code for access token"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://accounts.spotify.com/api/token",
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": REDIRECT_URI,
                    "client_id": CLIENT_ID,
                    "client_secret": CLIENT_SECRET,
                },
            )
            response.raise_for_status()
            token_data = response.json()
            access_token = token_data["access_token"]

            # Get user info
            user_response = await client.get(
                "https://api.spotify.com/v1/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            user_data = user_response.json()
            user_id = user_data.get("id")

            # Store token in memory
            user_tokens[user_id] = access_token

            return {"user_id": user_id, "access_token": access_token}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== DATA FETCHING ROUTES ====================


@app.get("/api/data/top-artists")
async def get_top_artists(
    user_id: str, time_range: str = "medium_term", limit: int = 50
):
    """Get user's top artists and save to fetched_data folder"""
    if user_id not in user_tokens:
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = user_tokens[user_id]
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.spotify.com/v1/me/top/artists",
                headers={"Authorization": f"Bearer {token}"},
                params={"time_range": time_range, "limit": limit},
            )
            response.raise_for_status()
            data = response.json()

            # Save data locally
            save_artist_data(user_id, data)

            return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/data/top-tracks")
async def get_top_tracks(
    user_id: str, time_range: str = "medium_term", limit: int = 50
):
    """Get user's top tracks"""
    if user_id not in user_tokens:
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = user_tokens[user_id]
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.spotify.com/v1/me/top/tracks",
                headers={"Authorization": f"Bearer {token}"},
                params={"time_range": time_range, "limit": limit},
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/data/playlists")
async def get_playlists(user_id: str, limit: int = 50):
    """Get user's playlists"""
    if user_id not in user_tokens:
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = user_tokens[user_id]
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.spotify.com/v1/me/playlists",
                headers={"Authorization": f"Bearer {token}"},
                params={"limit": limit},
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== FRONTEND ROUTES ====================


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve login page"""
    return get_login_page()


@app.get("/callback", response_class=HTMLResponse)
async def callback_page():
    """Serve OAuth callback page"""
    return get_callback_page()


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Serve authenticated dashboard page"""
    return get_dashboard_page()


# ==================== UTILITY FUNCTIONS ====================


def save_artist_data(user_id: str, data: dict) -> None:
    """Save artist data to fetched_data/{user_id}/artists_YYYY-MM-DD.json"""
    user_dir = DATA_DIR / user_id
    user_dir.mkdir(exist_ok=True)

    # Use today's date for filename
    date_str = datetime.now().strftime("%Y-%m-%d")
    file_path = user_dir / f"artists_{date_str}.json"

    # Save with formatting for readability
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
