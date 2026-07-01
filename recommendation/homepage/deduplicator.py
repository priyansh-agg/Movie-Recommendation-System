"""
Cross-section deduplication for the Netflix-style homepage.

Movies that appear in an earlier (higher-priority) section are removed
from all later sections.  This ensures a user never sees the same
movie card twice on the homepage.
"""

from recommendation.common.schemas import HomepageSection


def deduplicate_sections(
    sections: list[HomepageSection],
) -> list[HomepageSection]:
    """
    Remove duplicate movies across homepage sections.

    Priority rule: sections earlier in the list keep their movies.
    A movie appearing in "Top Picks" will **not** appear again in
    "Trending" or any genre row.

    Sections that become empty after deduplication are dropped entirely
    so the frontend never renders an empty row.

    Parameters
    ----------
    sections : list[HomepageSection]
        Ordered list of sections (highest priority first).

    Returns
    -------
    list[HomepageSection]
        Deduplicated sections with empty ones removed.
    """

    seen_tmdb_ids: set[int] = set()

    for section in sections:
        filtered = []
        for movie in section.movies:
            if movie.tmdbId is not None and movie.tmdbId not in seen_tmdb_ids:
                seen_tmdb_ids.add(movie.tmdbId)
                filtered.append(movie)
        section.movies = filtered

    # Drop sections that ended up empty after dedup.
    return [s for s in sections if s.movies]
