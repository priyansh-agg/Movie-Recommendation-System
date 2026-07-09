"""
Explanation generator for content-based recommendations.

Compares metadata between a liked movie and a recommended movie
to produce human-readable reasons.  Handles both old (with cast/crew)
and new (without cast/crew) dataset formats gracefully.
"""

from recommendation.content_based.loader import movie_metadata


def _to_tokens(value):
    """Convert a metadata field to a list of tokens."""
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        # Handle comma-separated ("Action, Drama") and space-separated ("Action Drama")
        if "," in value:
            return [t.strip().replace(" ", "").lower() for t in value.split(",") if t.strip()]
        return value.split()
    return []


# Pre-process genre/keyword columns into token lists at module load
# (safe for both old and new metadata formats)
for col in ["genres", "keywords"]:
    if col in movie_metadata.columns:
        movie_metadata[col] = movie_metadata[col].apply(_to_tokens)

# Cast and crew may not exist in the new TMDB_LARGE dataset
if "cast" in movie_metadata.columns:
    movie_metadata["cast"] = movie_metadata["cast"].apply(_to_tokens)
if "crew" in movie_metadata.columns:
    movie_metadata["crew"] = movie_metadata["crew"].apply(
        lambda x: x.split() if isinstance(x, str) else (x if isinstance(x, list) else [])
    )


def _shared_genres(movie1, movie2):
    g1 = movie1.get("genres", []) if isinstance(movie1, dict) else getattr(movie1, "genres", [])
    g2 = movie2.get("genres", []) if isinstance(movie2, dict) else getattr(movie2, "genres", [])
    if not isinstance(g1, list): g1 = []
    if not isinstance(g2, list): g2 = []
    return list(set(g1) & set(g2))


def _shared_keywords(movie1, movie2):
    k1 = movie1.get("keywords", []) if isinstance(movie1, dict) else getattr(movie1, "keywords", [])
    k2 = movie2.get("keywords", []) if isinstance(movie2, dict) else getattr(movie2, "keywords", [])
    if not isinstance(k1, list): k1 = []
    if not isinstance(k2, list): k2 = []
    return list(set(k1) & set(k2))


def _shared_cast(movie1, movie2):
    c1 = movie1.get("cast", []) if isinstance(movie1, dict) else getattr(movie1, "cast", [])
    c2 = movie2.get("cast", []) if isinstance(movie2, dict) else getattr(movie2, "cast", [])
    if not isinstance(c1, list): c1 = []
    if not isinstance(c2, list): c2 = []
    return list(set(c1) & set(c2))


def _same_director(movie1, movie2):
    d1 = movie1.get("crew", "") if isinstance(movie1, dict) else getattr(movie1, "crew", "")
    d2 = movie2.get("crew", "") if isinstance(movie2, dict) else getattr(movie2, "crew", "")
    if d1 and d1 == d2:
        return d1
    return None


def generate_explanation(source_index, recommended_index, similarity_score):
    """Generate human-readable reasons for a recommendation."""
    liked_movie = movie_metadata.iloc[source_index]
    recommended_movie = movie_metadata.iloc[recommended_index]

    reasons = []

    genres = _shared_genres(liked_movie, recommended_movie)
    if genres:
        reasons.append("Shared genres: " + ", ".join(genres[:3]))

    keywords = _shared_keywords(liked_movie, recommended_movie)
    if keywords:
        reasons.append("Common themes: " + ", ".join(keywords[:3]))

    cast = _shared_cast(liked_movie, recommended_movie)
    if cast:
        reasons.append("Featuring " + ", ".join(cast[:2]))

    director = _same_director(liked_movie, recommended_movie)
    if director:
        reasons.append(f"Directed by {director}")

    reasons.append(f"Similarity Score: {similarity_score:.0%}")

    return reasons