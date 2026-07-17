import pandas as pd
from recommendation.collaborative.loader import load_ratings
from recommendation.config import TRENDING_RECENCY_FRACTION

print("Loading...")
ratings_df = load_ratings()
ratings_df["timestamp"] = pd.to_numeric(ratings_df["timestamp"], errors="coerce")
print("Total ratings:", len(ratings_df))
print("NaN timestamps:", ratings_df["timestamp"].isna().sum())
ratings_df = ratings_df.dropna(subset=["timestamp"])

max_ts = ratings_df["timestamp"].max()
min_ts = ratings_df["timestamp"].min()
print("Max TS:", max_ts, "Min TS:", min_ts)
cutoff = max_ts - (max_ts - min_ts) * TRENDING_RECENCY_FRACTION
print("Cutoff:", cutoff)
recent = ratings_df[ratings_df["timestamp"] >= cutoff]
print("Recent ratings length:", len(recent))
