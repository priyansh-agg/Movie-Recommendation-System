import os
import requests

# Simple in-memory cache to avoid redundant HTTP calls.
# Critical for homepage performance where the same movie can appear
# in multiple engine passes before deduplication.
_poster_cache: dict[int, str] = {}


def fetch_poster(movie_id):
    """Fetch the movie poster URL from TMDB via the proxy API."""

    if movie_id in _poster_cache:
        return _poster_cache[movie_id]

    api_key = os.environ.get("TMDB_API_KEY", "")
    if not api_key:
        url = "https://via.placeholder.com/300x450?text=No+API+Key"
        _poster_cache[movie_id] = url
        return url

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
            url = "https://image.tmdb.org/t/p/original" + poster_path
            _poster_cache[movie_id] = url
            return url
    except requests.RequestException:
        pass

    url = "https://via.placeholder.com/300x450?text=No+Poster"
    _poster_cache[movie_id] = url
    return url