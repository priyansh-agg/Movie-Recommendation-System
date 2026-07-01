from typing import Optional, Any
from pydantic import BaseModel, Field


class Scores(BaseModel):
    content: Optional[float] = None
    collaborative: Optional[float] = None
    popularity: Optional[float] = None
    hybrid: Optional[float] = None


class Explanation(BaseModel):
    engine: str
    source_movie: Optional[str] = None
    reasons: list[str] = Field(default_factory=list)


class Recommendation(BaseModel):
    movieId: Optional[int] = None
    tmdbId: Optional[int] = None

    title: str
    poster: str

    scores: Scores

    # Keep metadata flexible.
    # TMDB datasets will evolve and we don't want to update the schema
    # every time a new field appears.
    metadata: dict[str, Any] = Field(default_factory=dict)

    explanation: Explanation
    source: str


class HomepageSection(BaseModel):
    """A single row on the Netflix-style homepage."""

    section_id: str          # e.g. "top_picks", "genre_action"
    title: str               # e.g. "Top Picks For You"
    section_type: str        # "personalized" | "trending" | "genre" | "editorial"
    movies: list[Recommendation] = Field(default_factory=list)