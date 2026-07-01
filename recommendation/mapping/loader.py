from pathlib import Path

import pandas as pd

from recommendation.content_based.loader import metadata_lookup
from recommendation.services.poster_service import fetch_poster

BASE_DIR = Path(__file__).resolve().parents[2]

LINKS_PATH = BASE_DIR / "datasets" / "movielens" / "links.csv"


def _load_links():
    """Load and clean the MovieLens → TMDB ID mapping table."""
    df = pd.read_csv(LINKS_PATH)
    df = df.dropna(subset=["tmdbId"])
    df["tmdbId"] = df["tmdbId"].astype(int)
    return df


links = _load_links()

movie_to_tmdb: dict[int, int] = dict(zip(links.movieId, links.tmdbId))
tmdb_to_movie: dict[int, int] = dict(zip(links.tmdbId, links.movieId))


def movie_to_tmdb_id(movie_id):
    """Convert a MovieLens movieId to a TMDB ID."""
    return movie_to_tmdb.get(movie_id)


def tmdb_to_movie_id(tmdb_id):
    """Convert a TMDB ID to a MovieLens movieId."""
    return tmdb_to_movie.get(tmdb_id)


def resolve_movie(movie_id):
    """
    Resolve a MovieLens movieId into a complete movie dict.

    Returns None if the movie cannot be mapped to TMDB or has
    no metadata in the content model.

    Returns
    -------
    dict | None
        Keys: movieId, tmdbId, title, poster, metadata.
    """
    tmdb_id = movie_to_tmdb_id(movie_id)
    if tmdb_id is None:
        return None

    metadata = metadata_lookup.get(tmdb_id)
    if metadata is None:
        return None

    return {
        "movieId": movie_id,
        "tmdbId": tmdb_id,
        "title": metadata.get("title", f"Movie {tmdb_id}"),
        "poster": fetch_poster(tmdb_id),
        "metadata": metadata,
    }