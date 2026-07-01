from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[2]

DATASET_DIR = BASE_DIR / "datasets" / "movielens"

RATINGS_PATH = DATASET_DIR / "ratings.csv"
MOVIES_PATH  = DATASET_DIR / "movies.csv"
LINKS_PATH   = DATASET_DIR / "links.csv"


def load_ratings():
    return pd.read_csv(RATINGS_PATH)


def load_movies():
    return pd.read_csv(MOVIES_PATH)


def load_links():
    return pd.read_csv(LINKS_PATH)