import os
from urllib.parse import urlencode

import httpx
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse

from app.services.frontend import (
    get_callback_page,
    get_dashboard_page,
    get_login_page,
)
from app.services.spotify import get_top_artists, get_top_tracks
from app.services.storage import StorageService

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
async def callback(code: str = Form(...), background_tasks: BackgroundTasks = BackgroundTasks()):
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

            # Trigger background task to ingest user data
            background_tasks.add_task(ingest_user_data, user_id, access_token)

            return {"user_id": user_id, "access_token": access_token}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==================== DATA FETCHING ROUTES ====================


@app.get("/api/data/top-artists")
async def top_artists_endpoint(
    user_id: str, time_range: str = "medium_term", limit: int = 50
):
    """Get user's top artists"""
    if user_id not in user_tokens:
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = user_tokens[user_id]
    try:
        data = await get_top_artists(token, time_range, limit)
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/data/top-tracks")
async def top_tracks_endpoint(
    user_id: str, time_range: str = "medium_term", limit: int = 50
):
    """Get user's top tracks"""
    if user_id not in user_tokens:
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = user_tokens[user_id]
    try:
        data = await get_top_tracks(token, time_range, limit)
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/data/playlists")
async def playlists_endpoint(user_id: str, limit: int = 50):
    """Get user's playlists"""
    if user_id not in user_tokens:
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = user_tokens[user_id]
    try:
        from app.services.spotify import get_playlists
        data = await get_playlists(token, limit)
        return data
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


# ==================== BACKGROUND TASKS ====================


async def ingest_user_data(user_id: str, access_token: str) -> None:
    """
    Background task to fetch and upload user data to GCS
    
    Args:
        user_id: Spotify user ID
        access_token: Spotify access token
    """
    try:
        # Initialize storage service
        storage_service = StorageService()
        
        # Fetch top artists and tracks
        artists_data = await get_top_artists(access_token, limit=50)
        tracks_data = await get_top_tracks(access_token, limit=50)
        
        # Upload to GCS
        storage_service.upload_json(artists_data, f"{user_id}/artists.json")
        storage_service.upload_json(tracks_data, f"{user_id}/tracks.json")
        
        print(f"Successfully ingested data for user {user_id}")
    except Exception as e:
        print(f"Error ingesting data for user {user_id}: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
