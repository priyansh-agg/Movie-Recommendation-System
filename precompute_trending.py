import json
import pandas as pd
from recommendation.collaborative.loader import load_ratings, DATASET_DIR
from recommendation.config import TRENDING_RECENCY_FRACTION
from recommendation.mapping.loader import movie_to_tmdb_id
import os

print("Loading ratings...")
ratings_df = load_ratings()
print("Parsing dates...")
ratings_df["timestamp"] = pd.to_datetime(ratings_df["timestamp"], errors="coerce")

print("Computing trending...")
max_ts = ratings_df["timestamp"].max()
min_ts = ratings_df["timestamp"].min()
cutoff = max_ts - (max_ts - min_ts) * TRENDING_RECENCY_FRACTION

recent = ratings_df[ratings_df["timestamp"] >= cutoff]
trending_counts = recent.groupby("movieId").size().reset_index(name="recent_count").sort_values("recent_count", ascending=False)

movies = []
for _, row in trending_counts.iterrows():
    if len(movies) >= 100:
        break
    movie_id = int(row["movieId"])
    tmdb_id = movie_to_tmdb_id(movie_id)
    if tmdb_id is not None:
        movies.append({"movie_id": movie_id, "tmdb_id": int(tmdb_id), "count": int(row["recent_count"])})

out_path = DATASET_DIR / "trending.json"
print(f"Saving {len(movies)} trending movies to {out_path}...")
with open(out_path, "w") as f:
    json.dump(movies, f)
print("Done!")
