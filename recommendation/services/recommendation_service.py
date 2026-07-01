import difflib

from recommendation.content_based.recommender import recommend as content_recommend
from recommendation.content_based.loader import movie_titles
from recommendation.hybrid.recommender import recommend as hybrid_recommend


class RecommendationService:
    """
    Public API for the recommendation system.

    This is the single entry point that FastAPI (Phase 3) will call.
    All internal engine details are hidden behind these three methods.
    """

    def recommend_similar(self, movies, top_n=10):
        """
        Content-based: "Movies like X".

        Uses the content engine directly — cosine similarity on
        movie metadata features (genres, keywords, cast, crew).

        Args:
            movies: List of movie title strings.
            top_n: Number of results.

        Returns:
            list[Recommendation]
        """
        return content_recommend(movies, top_n=top_n)

    def recommend_for_user(self, user_id, liked_movies=None, top_n=10):
        """
        Hybrid: Personalised recommendations for a user.

        Combines content-based (from ``liked_movies``) and collaborative
        filtering (from ``user_id``'s rating history) through the full
        hybrid pipeline: merge → normalize → rank.

        Args:
            user_id: MovieLens user ID (None for anonymous users).
            liked_movies: List of movie title strings the user liked.
            top_n: Number of results.

        Returns:
            list[Recommendation]
        """
        return hybrid_recommend(
            user_id=user_id,
            liked_movies=liked_movies,
            top_n=top_n,
        )

    def search(self, query, max_results=10):
        """
        Fuzzy search for movie titles.

        Uses exact substring matching first, then falls back to
        ``difflib.get_close_matches`` for approximate string matching
        so users don't need to type exact titles.

        Args:
            query: Search string.
            max_results: Maximum number of matches to return.

        Returns:
            list[dict]: Matching movies with ``title`` and ``tmdbId``.
        """
        if not query or not query.strip():
            return []

        all_titles = movie_titles["title"].tolist()
        query_lower = query.lower().strip()

        # ── Pass 1: exact substring matches (case-insensitive) ──────
        exact_matches = [
            title
            for title in all_titles
            if query_lower in title.lower()
        ]

        if len(exact_matches) >= max_results:
            return self._titles_to_results(exact_matches[:max_results])

        # ── Pass 2: fuzzy matching for remaining slots ──────────────
        remaining = max_results - len(exact_matches)
        fuzzy_matches = difflib.get_close_matches(
            query,
            all_titles,
            n=remaining + len(exact_matches),
            cutoff=0.4,
        )

        # Combine without duplicates — exact matches first.
        seen = set(exact_matches)
        combined = list(exact_matches)
        for title in fuzzy_matches:
            if title not in seen:
                combined.append(title)
                seen.add(title)
            if len(combined) >= max_results:
                break

        return self._titles_to_results(combined)

    @staticmethod
    def _titles_to_results(titles):
        """Convert title strings to result dicts with tmdbId."""
        results = []
        for title in titles:
            row = movie_titles[movie_titles["title"] == title]
            if not row.empty:
                results.append({
                    "title": title,
                    "tmdbId": int(row.iloc[0]["id"]),
                })
        return results
