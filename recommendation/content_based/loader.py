"""
Content-based model loader.

Loads pre-computed artifacts from ``recommendation/models/``:
    - similarity (dense matrix or sparse top-K dict)
    - rating (MinMaxScaled vote_avg + popularity)
    - movie_titles (id, title lookup table)
    - movie_metadata (full metadata DataFrame)

Supports both formats:
    - ``similarity.pkl`` (legacy dense NxN matrix)
    - ``similarity_sparse.pkl`` (Phase 8 sparse top-K dict)
"""

import os
import pickle

import pandas as pd

MODELS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "models"
)

# ── Similarity matrix (dense or sparse) ─────────────────────────────

_sparse_sim_path = os.path.join(MODELS_DIR, "similarity_sparse.pkl")
_dense_sim_path = os.path.join(MODELS_DIR, "similarity.pkl")

if os.path.exists(_sparse_sim_path):
    similarity_sparse = pickle.load(open(_sparse_sim_path, "rb"))
    similarity = None  # Not loaded to save memory
    SIMILARITY_MODE = "sparse"
else:
    similarity = pickle.load(open(_dense_sim_path, "rb"))
    similarity_sparse = None
    SIMILARITY_MODE = "dense"

# ── Rating data ─────────────────────────────────────────────────────

rating = pickle.load(
    open(os.path.join(MODELS_DIR, "rating.pkl"), "rb")
)

# ── Movie titles ────────────────────────────────────────────────────

movie_titles = pd.read_csv(
    os.path.join(MODELS_DIR, "movie_titles.csv")
)

movie_to_index = pd.Series(
    movie_titles.index,
    index=movie_titles["title"]
).to_dict()

# ── Movie metadata ──────────────────────────────────────────────────

movie_metadata = pickle.load(
    open(os.path.join(MODELS_DIR, "movie_metadata.pkl"), "rb")
)

metadata_lookup = movie_metadata.set_index("id").to_dict("index")