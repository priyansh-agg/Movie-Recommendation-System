import pandas as pd
from recommendation.collaborative.loader import load_ratings
from recommendation.config import TRENDING_RECENCY_FRACTION
from recommendation.mapping.loader import movie_to_tmdb_id

print("Loading...")
ratings_df = load_ratings()
ratings_df["timestamp"] = pd.to_numeric(ratings_df["timestamp"], errors="coerce")
max_ts = ratings_df["timestamp"].max()
min_ts = ratings_df["timestamp"].min()
cutoff = max_ts - (max_ts - min_ts) * TRENDING_RECENCY_FRACTION
recent = ratings_df[ratings_df["timestamp"] >= cutoff]
trending_counts = recent.groupby("movieId").size().reset_index(name="recent_count").sort_values("recent_count", ascending=False)
print("Trending counts length:", len(trending_counts))
print("First 5:")
for _, row in trending_counts.head().iterrows():
    movie_id = int(row["movieId"])
    tmdb = movie_to_tmdb_id(movie_id)
    print(movie_id, row["recent_count"], tmdb)
