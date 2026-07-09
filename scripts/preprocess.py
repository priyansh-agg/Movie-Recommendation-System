"""
Dataset Migration Pipeline: TMDB5000 + ML Small → TMDB Large + ML Latest.

Reads raw CSVs from ``datasets/`` and generates all model artifacts
that the recommendation engine needs.

Usage::

    python scripts/preprocess.py           # full pipeline
    python scripts/preprocess.py --skip-svd # skip SVD training (fast)

Output artifacts (written to ``recommendation/models/``):
    - movie_titles.csv       — id, title lookup
    - movie_metadata.pkl     — full metadata DataFrame
    - rating.pkl             — MinMaxScaled [vote_avg, popularity]
    - similarity_sparse.pkl  — top-K neighbours per movie (sparse)
    - svd_model.pkl          — retrained SVD on ML Latest ratings
"""

import argparse
import pickle
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from nltk.stem.porter import PorterStemmer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler

# ── Paths ───────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[1]
DATASETS = ROOT / "datasets"
MODELS = ROOT / "recommendation" / "models"
COLLAB_MODELS = ROOT / "recommendation" / "collaborative" / "models"

TMDB_LARGE = DATASETS / "TMDB_LARGE.csv"
ML_LARGE = DATASETS / "movielens_large"
ML_RATINGS = ML_LARGE / "rating.csv"
ML_MOVIES = ML_LARGE / "movie.csv"
ML_LINKS = ML_LARGE / "link.csv"

MODELS.mkdir(parents=True, exist_ok=True)
COLLAB_MODELS.mkdir(parents=True, exist_ok=True)

TOP_K_NEIGHBOURS = 50  # sparse similarity: keep top-K per movie

ps = PorterStemmer()


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# ====================================================================
# Step 1: Load & Clean TMDB Large
# ====================================================================
def load_tmdb():
    log("Loading TMDB_LARGE.csv...")
    df = pd.read_csv(TMDB_LARGE, low_memory=False)
    log(f"  Raw: {len(df):,} rows")

    # Filter
    df = df[df["status"] == "Released"]
    df = df[df["adult"].astype(str).str.lower() == "false"]
    df["vote_count"] = pd.to_numeric(df["vote_count"], errors="coerce").fillna(0)
    df = df[df["vote_count"] >= 10]
    df = df.dropna(subset=["title", "overview"])
    df = df.drop_duplicates(subset=["id"])

    # Clean types
    df["id"] = pd.to_numeric(df["id"], errors="coerce")
    df = df.dropna(subset=["id"])
    df["id"] = df["id"].astype(int)

    df["vote_average"] = pd.to_numeric(df["vote_average"], errors="coerce").fillna(0)
    df["popularity"] = pd.to_numeric(df["popularity"], errors="coerce").fillna(0)
    df["runtime"] = pd.to_numeric(df["runtime"], errors="coerce").fillna(0)

    df["overview"] = df["overview"].fillna("")
    df["genres"] = df["genres"].fillna("")
    df["keywords"] = df["keywords"].fillna("")
    df["tagline"] = df["tagline"].fillna("")
    df["release_date"] = df["release_date"].fillna("")
    df["poster_path"] = df["poster_path"].fillna("")

    # Extract release year
    df["release_year"] = (
        pd.to_datetime(df["release_date"], errors="coerce")
        .dt.year.fillna(0)
        .astype(int)
    )

    log(f"  After filtering: {len(df):,} movies")
    return df.reset_index(drop=True)


# ====================================================================
# Step 2: Merge with MovieLens via link.csv
# ====================================================================
def merge_with_movielens(tmdb):
    log("Loading MovieLens links...")
    links = pd.read_csv(ML_LINKS)
    links = links.dropna(subset=["tmdbId"])
    links["tmdbId"] = links["tmdbId"].astype(int)

    log(f"  Links: {len(links):,} mappings")

    # Inner join: only movies that exist in BOTH datasets
    merged = tmdb.merge(links, left_on="id", right_on="tmdbId", how="inner")

    # Deduplicate by TMDB ID (keep highest vote_count)
    before = len(merged)
    merged = merged.sort_values("vote_count", ascending=False)
    merged = merged.drop_duplicates(subset="id", keep="first")
    merged = merged.sort_index()
    if len(merged) < before:
        log(f"  Removed {before - len(merged)} duplicate TMDB IDs")

    log(f"  After merge: {len(merged):,} movies with ML + TMDB data")

    return merged


# ====================================================================
# Step 3: Build Content Tags
# ====================================================================
def clean_token(text):
    """Remove spaces and special chars from a tag token."""
    return text.strip().replace(" ", "").replace("-", "").lower()


def build_tags(row):
    """
    Build tag string for CountVectorizer.

    Formula (adapted for no cast/crew in TMDB_LARGE):
        overview + genres*3 + keywords*3 + tagline
    """
    overview = " ".join(str(row["overview"]).lower().split())

    # TMDB_LARGE genres: "Action, Science Fiction, Adventure"
    genres_raw = str(row["genres"])
    genre_tokens = " ".join(clean_token(g) for g in genres_raw.split(",") if g.strip())

    keywords_raw = str(row["keywords"])
    kw_tokens = " ".join(clean_token(k) for k in keywords_raw.split(",") if k.strip())

    tagline = " ".join(str(row["tagline"]).lower().split())

    # Weight: genres x3, keywords x3, tagline x1
    parts = [
        overview,
        genre_tokens, genre_tokens, genre_tokens,
        kw_tokens, kw_tokens, kw_tokens,
        tagline,
    ]
    return " ".join(parts)


def stem_text(text):
    return " ".join(ps.stem(w) for w in text.split())


def preprocess_content(df):
    log("Building content tags...")
    df = df.copy()

    df["tags"] = df.apply(build_tags, axis=1)
    log("  Stemming...")
    df["tags"] = df["tags"].apply(stem_text)

    return df


# ====================================================================
# Step 4: Vectorise & Sparse Similarity
# ====================================================================
def build_sparse_similarity(df, top_k=TOP_K_NEIGHBOURS):
    log(f"Vectorising {len(df):,} movies (CountVectorizer)...")
    cv = CountVectorizer(max_features=10000, stop_words="english")
    vectors = cv.fit_transform(df["tags"])

    log(f"  Feature matrix: {vectors.shape}")
    log(f"Computing sparse similarity (top-{top_k} neighbours)...")

    n = vectors.shape[0]
    # Process in batches to avoid memory explosion
    batch_size = 500
    sparse_sim = {}

    for start in range(0, n, batch_size):
        end = min(start + batch_size, n)
        # Compute similarity of this batch against ALL movies
        batch_sim = cosine_similarity(vectors[start:end], vectors)

        for i in range(start, end):
            row = batch_sim[i - start]
            # Get top-K indices (excluding self)
            top_indices = np.argsort(row)[::-1][1:top_k + 1]
            top_scores = row[top_indices]
            sparse_sim[i] = list(zip(top_indices.tolist(), top_scores.tolist()))

        if (end % 5000) == 0 or end == n:
            log(f"  Processed {end:,}/{n:,} movies")

    return sparse_sim


# ====================================================================
# Step 5: Rating normalisation
# ====================================================================
def build_ratings(df):
    log("Normalising ratings (MinMaxScaler)...")
    scaler = MinMaxScaler()
    rating_data = scaler.fit_transform(df[["vote_average", "popularity"]].values)
    return rating_data


# ====================================================================
# Step 6: SVD Model Training
# ====================================================================
def train_svd():
    log("Loading MovieLens ratings (20M rows)...")
    t0 = time.time()
    ratings = pd.read_csv(ML_RATINGS)
    log(f"  Loaded {len(ratings):,} ratings in {time.time() - t0:.1f}s")

    from surprise import Dataset, Reader, SVD, accuracy
    from surprise.model_selection import train_test_split as svd_split

    reader = Reader(rating_scale=(0.5, 5))
    data = Dataset.load_from_df(
        ratings[["userId", "movieId", "rating"]], reader
    )

    log("Splitting train/test (80/20)...")
    train_set, test_set = svd_split(data, test_size=0.2, random_state=42)

    log("Training SVD (n_factors=150, n_epochs=30)...")
    log("  This will take 15-25 minutes...")
    t0 = time.time()
    model = SVD(n_factors=150, n_epochs=30, random_state=42)
    model.fit(train_set)
    elapsed = time.time() - t0
    log(f"  SVD training complete in {elapsed / 60:.1f} minutes")

    log("Evaluating...")
    preds = model.test(test_set)
    rmse = accuracy.rmse(preds, verbose=False)
    mae = accuracy.mae(preds, verbose=False)
    log(f"  RMSE: {rmse:.4f}")
    log(f"  MAE:  {mae:.4f}")
    log(f"  User factors: {model.pu.shape}")
    log(f"  Item factors: {model.qi.shape}")

    return model


# ====================================================================
# Main Pipeline
# ====================================================================
def main():
    parser = argparse.ArgumentParser(description="Preprocess datasets")
    parser.add_argument(
        "--skip-svd", action="store_true",
        help="Skip SVD training (use existing model)"
    )
    args = parser.parse_args()

    log("=" * 60)
    log("Dataset Migration Pipeline")
    log("=" * 60)

    # Step 1: Load TMDB
    tmdb = load_tmdb()

    # Step 2: Merge with MovieLens
    merged = merge_with_movielens(tmdb)

    # Step 3: Content preprocessing
    processed = preprocess_content(merged)

    # Save movie_titles.csv (id + title)
    titles_df = processed[["id", "title"]].copy()
    titles_df.to_csv(MODELS / "movie_titles.csv", index=False)
    log(f"Saved movie_titles.csv ({len(titles_df):,} movies)")

    # Save movie_metadata.pkl (full metadata for the homepage/API)
    metadata_cols = [
        "id", "title", "overview", "genres", "keywords", "tagline",
        "vote_average", "vote_count", "popularity", "release_date",
        "release_year", "runtime", "original_language", "poster_path",
    ]
    meta_df = processed[[c for c in metadata_cols if c in processed.columns]].copy()
    pickle.dump(meta_df, open(MODELS / "movie_metadata.pkl", "wb"))
    log(f"Saved movie_metadata.pkl")

    # Step 4: Similarity
    sparse_sim = build_sparse_similarity(processed)
    pickle.dump(sparse_sim, open(MODELS / "similarity_sparse.pkl", "wb"))
    log(f"Saved similarity_sparse.pkl ({len(sparse_sim):,} movies)")

    # Step 5: Rating normalisation
    rating_data = build_ratings(processed)
    pickle.dump(rating_data, open(MODELS / "rating.pkl", "wb"))
    log(f"Saved rating.pkl")

    # Step 6: SVD
    if args.skip_svd:
        log("Skipping SVD training (--skip-svd)")
    else:
        model = train_svd()
        pickle.dump(model, open(COLLAB_MODELS / "svd_model.pkl", "wb"))
        log(f"Saved svd_model.pkl")

    log("")
    log("=" * 60)
    log("Pipeline complete!")
    log("=" * 60)


if __name__ == "__main__":
    main()
