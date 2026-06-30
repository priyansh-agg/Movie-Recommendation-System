import os
import requests


def fetch_poster(movie_id):
    """Fetch the movie poster URL from TMDB via the proxy API."""
    api_key = os.environ.get("TMDB_API_KEY", "")
    if not api_key:
        return "https://via.placeholder.com/300x450?text=No+API+Key"

    path = f"/movie/{movie_id}?api_key={api_key}"
    try:
        res = requests.get(
            f"https://weathered.appukid69.workers.dev/?path={path}",
            timeout=10,
        )
        res.raise_for_status()
        data = res.json()
        poster_path = data.get("poster_path")
        if poster_path:
            return "https://image.tmdb.org/t/p/original" + poster_path
    except requests.RequestException:
        pass

    return "https://via.placeholder.com/300x450?text=No+Poster"