import os
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# --- Pydantic Models for Data Validation ---
class ArtistSearchRequest(BaseModel):
    artist_name: str

# This can be expanded to define the expected response structure for better type hinting and documentation

# --- FastAPI App Initialization ---
app = FastAPI()

SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")

async def get_spotify_token():
    """Authenticates with Spotify and returns an access token asynchronously."""
    auth_url = "https://accounts.spotify.com/api/token"
    auth_data = {
        'grant_type': 'client_credentials',
        'client_id': SPOTIFY_CLIENT_ID,
        'client_secret': SPOTIFY_CLIENT_SECRET,
    }
    async with httpx.AsyncClient() as client:
        try:
            auth_response = await client.post(auth_url, data=auth_data)
            auth_response.raise_for_status()
            return auth_response.json()['access_token']
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=502, detail=f"Spotify auth failed: {e}")

@app.post("/search-artist")
async def search_artist(search_request: ArtistSearchRequest):
    """
    Endpoint to search for an artist on Spotify.
    Receives a JSON body with 'artist_name' and returns the first result.
    """
    try:
        token = await get_spotify_token()
        headers = {'Authorization': f'Bearer {token}'}
        search_url = "https://api.spotify.com/v1/search"
        params = {'q': search_request.artist_name, 'type': 'artist', 'limit': 1}

        async with httpx.AsyncClient() as client:
            search_response = await client.get(search_url, headers=headers, params=params)
            search_response.raise_for_status()

        search_results = search_response.json()
        artists = search_results.get('artists', {}).get('items', [])

        if not artists:
            raise HTTPException(
                status_code=404,
                detail=f"No artist found for '{search_request.artist_name}'"
            )

        return artists[0]

    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Error from Spotify API: {e.response.text}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")