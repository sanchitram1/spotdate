import logging
import os
import secrets
import sys
from urllib.parse import urlencode

import httpx
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.services.frontend import get_dashboard_page, get_login_page
from app.services.spotify import get_top_artists, get_top_tracks
from app.services.storage import StorageService

load_dotenv()

# Spotify credentials
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")

# Spotify scopes
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
# Maps session_token -> {user_id, access_token}
sessions = {}

app = FastAPI()
app.add_middleware(ProxyHeadersMiddleware)

# Create the logger
logging.basicConfig(
    level=logging.INFO, format="%(levelname)s: %(message)s", stream=sys.stdout
)
logger = logging.getLogger(__name__)

# ==================== HELPER FUNCTIONS ====================


def get_user_id_from_session(request: Request) -> tuple[str, str]:
    """Extract user_id and access_token from session cookie"""
    session_token = request.cookies.get("session")
    logger.debug(f"Checking session: token={session_token}")
    if not session_token or session_token not in sessions:
        logger.debug("Session not found")
        raise HTTPException(status_code=401, detail="Not authenticated")
    session_data = sessions[session_token]
    user_id = session_data["user_id"]
    access_token = session_data["access_token"]
    logger.debug(f"Found user_id: {user_id}")
    return user_id, access_token


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


# 2. SIMPLIFY THE CALLBACK (Remove the HTML/JS Middleman)
# This replaces BOTH your @app.get('/callback') and @app.post('/api/auth/callback')
@app.get("/callback")
async def callback(code: str, background_tasks: BackgroundTasks):
    """
    Direct Server-Side Callback.
    No HTML/JS middleman means no 'fetch' errors and no CORS issues.
    """
    try:
        async with httpx.AsyncClient() as client:
            # Exchange Code for Token using REAL Spotify URL
            response = await client.post(
                "https://accounts.spotify.com/api/token",
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": REDIRECT_URI,
                    "client_id": CLIENT_ID,
                    "client_secret": CLIENT_SECRET,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            token_data = response.json()
            access_token = token_data["access_token"]

            # Get User Profile
            user_response = await client.get(
                "https://api.spotify.com/v1/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            user_data = user_response.json()
            user_id = user_data.get("id")

            # Background Task
            background_tasks.add_task(ingest_user_data, user_id, access_token)

            # Create session token with both user_id and access_token
            session_token = secrets.token_urlsafe(32)
            sessions[session_token] = {"user_id": user_id, "access_token": access_token}
            logger.debug(f"Session created for user {user_id}: {session_token}")

            # Redirect with session cookie
            response = RedirectResponse(url="/dashboard")
            response.set_cookie(
                key="session",
                value=session_token,
                httponly=True,
                secure=False,  # Allow HTTP for development/proxy scenarios
                samesite="lax",
                max_age=30 * 24 * 60 * 60,  # 30 days
            )
            logger.debug("Cookie set")
            return response

    except Exception as e:
        # This will show up in Cloud Run logs
        logger.error(f"Auth Failed: {e}")
        raise HTTPException(status_code=400, detail="Authentication failed")


# ==================== DATA FETCHING ROUTES ====================


@app.get("/api/data/top-artists")
async def top_artists_endpoint(
    request: Request, time_range: str = "medium_term", limit: int = 50
):
    """Get user's top artists"""
    user_id, token = get_user_id_from_session(request)
    try:
        data = await get_top_artists(token, time_range, limit)
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/data/top-tracks")
async def top_tracks_endpoint(
    request: Request, time_range: str = "medium_term", limit: int = 50
):
    """Get user's top tracks"""
    user_id, token = get_user_id_from_session(request)
    try:
        data = await get_top_tracks(token, time_range, limit)
        return data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/data/playlists")
async def playlists_endpoint(request: Request, limit: int = 50):
    """Get user's playlists"""
    user_id, token = get_user_id_from_session(request)
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


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Serve authenticated dashboard page"""
    # Check if user is authenticated
    try:
        get_user_id_from_session(request)
    except HTTPException:
        # If not authenticated, redirect to login
        return RedirectResponse(url="/")
    return get_dashboard_page()


@app.post("/api/auth/logout")
async def logout(request: Request):
    """Logout user and clear session"""
    session_token = request.cookies.get("session")
    if session_token and session_token in sessions:
        del sessions[session_token]
    response = {"status": "logged out"}
    response_obj = JSONResponse(response)
    response_obj.delete_cookie("session")
    return response_obj


@app.get("/debug-vars")
def debug_vars():
    return {
        "client_id_exists": os.environ.get("SPOTIFY_CLIENT_ID") is not None,
        "redirect_uri": os.environ.get("SPOTIFY_REDIRECT_URI"),
        "all_keys": list(os.environ.keys()),
    }


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

        logger.info(f"Successfully ingested data for user {user_id}")
    except Exception as e:
        logger.error(f"Error ingesting data for user {user_id}: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
