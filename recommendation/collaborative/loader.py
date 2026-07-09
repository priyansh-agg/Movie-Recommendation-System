"""
MovieLens data loader.

Points to ``datasets/movielens_large/`` (MovieLens Latest).
Falls back to ``datasets/movielens/`` (MovieLens Small) if the
large dataset is not available.
"""

from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]

# Prefer large dataset, fall back to small
LARGE_DIR = BASE_DIR / "datasets" / "movielens_large"
SMALL_DIR = BASE_DIR / "datasets" / "movielens"

if (LARGE_DIR / "rating.csv").exists():
    DATASET_DIR = LARGE_DIR
    RATINGS_FILE = "rating.csv"
    MOVIES_FILE = "movie.csv"
    LINKS_FILE = "link.csv"
else:
    DATASET_DIR = SMALL_DIR
    RATINGS_FILE = "ratings.csv"
    MOVIES_FILE = "movies.csv"
    LINKS_FILE = "links.csv"


def load_ratings():
    return pd.read_csv(DATASET_DIR / RATINGS_FILE)


def load_movies():
    return pd.read_csv(DATASET_DIR / MOVIES_FILE)


def load_links():
    return pd.read_csv(DATASET_DIR / LINKS_FILE)