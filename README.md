<div align="center">

# CINEMATIC

### A Netflix-Style Hybrid Movie Recommendation System

<img src="docs/hero_banner.jpg" alt="CINEMATIC — Movie Recommendation System" width="100%" />

[![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-6.0-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://typescriptlang.org)
[![PostgreSQL](https://img.shields.io/badge/Supabase-PostgreSQL-3FCF8E?style=for-the-badge&logo=supabase&logoColor=white)](https://supabase.com)
[![Redis](https://img.shields.io/badge/Redis-Cache-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io)

**Content-Based Filtering** | **Collaborative Filtering (SVD)** | **Hybrid Ranking Engine** | **20M+ Ratings**

[Features](#features) · [Architecture](#architecture) · [Quick Start](#quick-start) · [API Reference](#api-reference) · [Tech Stack](#tech-stack)

</div>

---

## Overview

**CINEMATIC** is a production-grade movie recommendation system that combines three machine learning approaches into a single hybrid engine, serving personalized recommendations through a Netflix-inspired dark-themed UI.

The system processes **20M+ ratings** from the MovieLens dataset and **50K+ movie metadata entries** from TMDB to deliver sub-100ms recommendations via a Redis-cached FastAPI backend and a React 19 frontend with glassmorphism design, Framer Motion animations, and responsive layouts.

---

## Features

<table>
<tr>
<td width="50%">

### Recommendation Engine
- **Hybrid scoring** — Content (50%) + Collaborative (35%) + Popularity (15%)
- **Cold-start handling** — Graceful degradation when data is sparse
- **Content-based filtering** — Cosine similarity on TF-IDF genre/keyword vectors
- **Collaborative filtering** — SVD matrix factorization (Surprise library)
- **Explainable recommendations** — "Because you watched X" with reasoning

</td>
<td width="50%">

### User Experience
- **Netflix-style homepage** — 10+ personalized sections, hero banner
- **Cinematic dark theme** — Glassmorphism, ambient orbs, smooth transitions
- **Interactive onboarding** — Pick 10+ movies to calibrate taste
- **Movie detail pages** — Ratings, watchlist, similar movies
- **Real-time search** — Debounced title search with instant results
- **Framer Motion animations** — Page transitions, stagger reveals, hover effects

</td>
</tr>
<tr>
<td width="50%">

### Backend Infrastructure
- **FastAPI REST API** — 15+ endpoints with OpenAPI docs
- **Redis caching** — Homepage served in 32ms (vs 2s uncached)
- **Supabase PostgreSQL** — User profiles, ratings, watchlists
- **JWT authentication** — Access + refresh token rotation
- **Startup pre-warming** — Cache populated before first request

</td>
<td width="50%">

### Data Pipeline
- **20M+ MovieLens ratings** processed via pandas
- **TMDB metadata** — Posters, overviews, genres, cast
- **Sparse similarity matrix** — Top-50 neighbors per movie
- **Pre-computed trending** — Recency-weighted activity analysis
- **Automated evaluation** — Precision@K, Recall@K, Diversity metrics

</td>
</tr>
</table>

---

## Architecture

```mermaid
graph TB
    subgraph Client["Frontend — React 19 + TypeScript"]
        UI["Cinematic UI<br/>Framer Motion + Zustand"]
        API_CLIENT["Axios Client<br/>JWT Interceptors"]
    end

    subgraph Server["Backend — FastAPI"]
        AUTH["Auth Router<br/>JWT + bcrypt"]
        REC["Recommendations Router"]
        SEARCH["Search Router"]
        FEED["Feedback Router"]
        USERS["Users Router"]
    end

    subgraph Cache["Caching Layer"]
        REDIS[("Redis<br/>TTL: 1hr homepage<br/>1hr similar")]
    end

    subgraph ML["Recommendation Engine"]
        HYBRID["Hybrid Recommender"]
        CONTENT["Content-Based<br/>TF-IDF + Cosine Sim"]
        COLLAB["Collaborative<br/>SVD (Surprise)"]
        MERGER["Score Merger"]
        RANKER["Normalizer + Ranker"]
    end

    subgraph Data["Data Layer"]
        PG[("Supabase<br/>PostgreSQL")]
        MODELS[("ML Models<br/>similarity.pkl<br/>rating.pkl")]
        TMDB[("TMDB API<br/>Posters + Metadata")]
    end

    UI --> API_CLIENT
    API_CLIENT --> AUTH
    API_CLIENT --> REC
    API_CLIENT --> SEARCH
    API_CLIENT --> FEED
    API_CLIENT --> USERS

    REC --> REDIS
    REDIS -.->|miss| HYBRID
    HYBRID --> CONTENT
    HYBRID --> COLLAB
    CONTENT --> MERGER
    COLLAB --> MERGER
    MERGER --> RANKER

    AUTH --> PG
    USERS --> PG
    FEED --> PG
    CONTENT --> MODELS
    COLLAB --> MODELS
    SEARCH --> TMDB

    style Client fill:#1a1a2e,stroke:#6366f1,color:#f0f0f5
    style Server fill:#12121a,stroke:#818cf8,color:#f0f0f5
    style Cache fill:#1a1a2e,stroke:#ef4444,color:#f0f0f5
    style ML fill:#12121a,stroke:#22c55e,color:#f0f0f5
    style Data fill:#1a1a2e,stroke:#fbbf24,color:#f0f0f5
```

---

## Recommendation Pipeline

```mermaid
flowchart LR
    A["User Input<br/>liked movies / user ID"] --> B{"Has liked<br/>movies?"}
    B -->|Yes| C["Content-Based<br/>Engine"]
    B -->|No| D{"Has user ID<br/>with ratings?"}

    D -->|Yes| E["Collaborative<br/>Engine"]
    D -->|No| F["Cold Start<br/>Popular + Trending"]

    C --> G["30 Content<br/>Candidates"]
    E --> H["30 Collab<br/>Candidates"]

    G --> I["Merge by<br/>TMDB ID"]
    H --> I

    I --> J["Normalize<br/>Scores 0→1"]
    J --> K["Weighted Hybrid<br/>C:50% + CF:35% + P:15%"]
    K --> L["Top-N<br/>Ranked Results"]

    style A fill:#6366f1,stroke:#818cf8,color:#fff
    style C fill:#3b82f6,stroke:#60a5fa,color:#fff
    style E fill:#8b5cf6,stroke:#a78bfa,color:#fff
    style F fill:#f59e0b,stroke:#fbbf24,color:#000
    style L fill:#22c55e,stroke:#4ade80,color:#000
```

---

## Homepage Section Builder

```mermaid
flowchart TD
    START["Homepage Request"] --> AUTH_CHECK{"Authenticated?"}

    AUTH_CHECK -->|Yes| P1["Continue Watching"]
    AUTH_CHECK -->|Yes| P2["Top Picks For You<br/>(Hybrid Engine)"]
    AUTH_CHECK -->|Yes| P3["Because You Watched X<br/>(Content-Based)"]
    AUTH_CHECK -->|Yes| P4["Your Watchlist"]

    AUTH_CHECK -->|No| SKIP["Skip personalized"]

    P1 --> UNIVERSAL
    P2 --> UNIVERSAL
    P3 --> UNIVERSAL
    P4 --> UNIVERSAL
    SKIP --> UNIVERSAL

    UNIVERSAL["Universal Sections"]
    UNIVERSAL --> U1["Trending Now"]
    UNIVERSAL --> U2["Popular This Week"]
    UNIVERSAL --> U3["Genre Rows x 4-6"]
    UNIVERSAL --> U4["New Releases"]
    UNIVERSAL --> U5["Top Rated Editorial"]

    U1 --> DEDUP["Deduplicator<br/>Priority-based"]
    U2 --> DEDUP
    U3 --> DEDUP
    U4 --> DEDUP
    U5 --> DEDUP

    DEDUP --> CACHE["Redis Cache<br/>TTL: 1 hour"]
    CACHE --> RESPONSE["JSON Response<br/>10-15 sections"]

    style START fill:#6366f1,stroke:#818cf8,color:#fff
    style CACHE fill:#dc382d,stroke:#ef4444,color:#fff
    style RESPONSE fill:#22c55e,stroke:#4ade80,color:#000
```

---

## Quick Start

### Prerequisites

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.13+ | Backend & ML engine |
| Node.js | 20+ | Frontend build |
| Redis | 7+ | Caching layer |
| PostgreSQL | 15+ | User data (via Supabase) |

### 1. Clone & Install

```bash
git clone https://github.com/priyansh-agg/Movie-Recommendation-System.git
cd Movie-Recommendation-System

# Backend dependencies
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend dependencies
cd frontend && npm install && cd ..
```

### 2. Environment Setup

Create a `.env` file in the project root:

```env
# Database (Supabase)
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT.supabase.co:5432/postgres

# Security
JWT_SECRET_KEY=your-secret-key-min-32-chars

# CORS (comma-separated origins)
CORS_ORIGINS=http://localhost:5173,http://localhost:5174

# Redis
REDIS_URL=redis://localhost:6379/0
```

### 3. Download Datasets

Download the [MovieLens 20M dataset](https://grouplens.org/datasets/movielens/20m/) and place files in `datasets/movielens/`:

```
datasets/
├── movielens/
│   ├── movies.csv
│   ├── ratings.csv
│   └── links.csv
└── tmdb_5000_movies.csv
```

### 4. Train Models

```bash
# Run the preprocessing and training notebooks
jupyter notebook notebooks/system.ipynb   # Feature engineering
jupyter notebook notebooks/trainer.ipynb  # SVD model training
```

This generates the model files in `recommendation/models/`:
- `similarity_sparse.pkl` — Sparse cosine similarity matrix
- `rating.pkl` — Trained SVD model
- `movie_metadata.pkl` — Processed metadata
- `movie_titles.csv` — Title index

### 5. Start Services

```bash
# Terminal 1: Redis
redis-server

# Terminal 2: Backend API
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 3: Frontend
cd frontend && npm run dev
```

Open **http://localhost:5173** and explore.

---

## API Reference

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/register` | Create account |
| `POST` | `/api/v1/auth/login` | Get JWT tokens |
| `POST` | `/api/v1/auth/refresh` | Refresh access token |

### Recommendations

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/recommendations/homepage` | Netflix-style homepage (10+ sections) |
| `GET` | `/api/v1/recommendations/similar?movies=Inception` | Content-based similar movies |
| `GET` | `/api/v1/recommendations/for-user` | Personalized hybrid recommendations |

### Search & Discovery

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/search?q=batman&max_results=10` | Title search |

### User Actions

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/users/me` | Get profile |
| `PUT` | `/api/v1/users/me` | Update preferences |
| `POST` | `/api/v1/users/onboarding` | Submit onboarding selections |
| `POST` | `/api/v1/feedback/rate` | Rate a movie (1-5) |
| `POST` | `/api/v1/feedback/like` | Like a movie |
| `POST` | `/api/v1/feedback/watchlist` | Add/remove from watchlist |
| `POST` | `/api/v1/feedback/watched` | Mark as watched |

> Full interactive docs available at **http://localhost:8000/docs** (Swagger UI)

---

## Tech Stack

```mermaid
graph LR
    subgraph Frontend
        REACT["React 19"]
        TS["TypeScript 6"]
        FRAMER["Framer Motion"]
        ZUSTAND["Zustand"]
        TANSTACK["TanStack Query"]
        VITE["Vite 8"]
    end

    subgraph Backend
        FASTAPI["FastAPI"]
        PYDANTIC["Pydantic v2"]
        JOSE["python-jose<br/>JWT"]
        PASSLIB["passlib<br/>bcrypt"]
    end

    subgraph ML
        SKLEARN["scikit-learn<br/>TF-IDF + Cosine"]
        SURPRISE["Surprise<br/>SVD"]
        PANDAS["pandas + numpy"]
        NLTK["NLTK<br/>Text Processing"]
    end

    subgraph Infra
        SUPABASE["Supabase<br/>PostgreSQL"]
        REDIS_S["Redis 7"]
        SQLALCHEMY["SQLAlchemy"]
    end

    REACT --> FASTAPI
    FASTAPI --> SKLEARN
    FASTAPI --> SURPRISE
    FASTAPI --> SUPABASE
    FASTAPI --> REDIS_S

    style Frontend fill:#1a1a2e,stroke:#61DAFB,color:#f0f0f5
    style Backend fill:#12121a,stroke:#009688,color:#f0f0f5
    style ML fill:#1a1a2e,stroke:#f59e0b,color:#f0f0f5
    style Infra fill:#12121a,stroke:#22c55e,color:#f0f0f5
```

---

## Project Structure

```
.
├── api/                          # FastAPI application
│   ├── auth/                     # JWT authentication
│   │   ├── jwt_handler.py        # Token creation & verification
│   │   ├── router.py             # Login / register / refresh
│   │   └── schemas.py            # Request/response models
│   ├── routers/                  # API route handlers
│   │   ├── recommendations.py    # Homepage, similar, for-user
│   │   ├── search.py             # Title search
│   │   ├── users.py              # Profile & onboarding
│   │   └── feedback.py           # Rate, like, watchlist
│   ├── dependencies.py           # DI container & auth guards
│   └── main.py                   # App entry point, CORS, lifespan
│
├── recommendation/               # ML recommendation engine
│   ├── content_based/            # TF-IDF cosine similarity
│   ├── collaborative/            # SVD matrix factorization
│   ├── hybrid/                   # Merge → Normalize → Rank
│   │   ├── merger.py             # Combine candidates by TMDB ID
│   │   ├── normalizer.py         # Min-max score normalization
│   │   ├── ranker.py             # Weighted hybrid scoring
│   │   └── recommender.py        # Pipeline orchestrator
│   ├── homepage/                 # Netflix-style section builder
│   │   ├── orchestrator.py       # 10+ section assembly
│   │   ├── sections.py           # Trending, popular, genre, etc.
│   │   └── deduplicator.py       # Cross-section dedup
│   ├── user/                     # User intelligence layer
│   │   ├── profile_service.py    # Profile management
│   │   ├── onboarding.py         # First-run movie picker
│   │   └── interaction_service.py # Rating/like/watchlist logic
│   ├── db/                       # Data layer
│   │   ├── postgres_repository.py # Supabase user repository
│   │   ├── redis_cache.py        # Cache-aside with TTL
│   │   └── session.py            # SQLAlchemy session
│   ├── evaluation/               # Quality metrics
│   │   ├── evaluator.py          # Precision@K, Recall@K
│   │   └── diversity.py          # ILS diversity scoring
│   ├── services/                 # Shared services
│   │   ├── recommendation_service.py
│   │   └── poster_service.py     # TMDB poster fetching
│   └── config.py                 # All tunable hyperparameters
│
├── frontend/                     # React 19 + TypeScript UI
│   └── src/
│       ├── api/                  # Axios client, typed endpoints
│       ├── components/
│       │   ├── ui/               # Button, Input, Toast, Loader, GlassCard
│       │   ├── movie/            # MovieCard, MovieRow, MovieGrid, RatingStars
│       │   ├── home/             # HeroBanner, HomepageRows
│       │   ├── layout/           # Navbar, PageTransition
│       │   └── auth/             # ProtectedRoute
│       ├── pages/                # Home, Detail, Search, Auth, Profile, etc.
│       ├── stores/               # Zustand auth store
│       └── hooks/                # useDebounce
│
├── notebooks/                    # Jupyter training notebooks
│   ├── system.ipynb              # Feature engineering pipeline
│   ├── trainer.ipynb             # SVD model training
│   └── ranking.ipynb             # Ranking experiments
│
├── datasets/                     # MovieLens + TMDB data
├── scripts/                      # DB init, preprocessing
└── test/                         # Verification scripts
```

---

## Performance

| Metric | Value |
|--------|-------|
| Homepage response (cached) | **32ms** |
| Homepage response (cold) | **1.8s** |
| Similar movies | **< 500ms** |
| Search | **< 100ms** |
| Dataset size | **20M+ ratings** |
| Movie catalog | **50K+ movies** |
| Startup time (models) | **~12s** |
| Cache TTL | **1 hour** |

---

## Hybrid Scoring Formula

$$S_{hybrid} = w_c \cdot \hat{s}_{content} + w_{cf} \cdot \hat{s}_{collab} + w_p \cdot \hat{s}_{popularity}$$

Where:
- $\hat{s}$ = min-max normalized score per dimension
- Default weights: $w_c = 0.50$, $w_{cf} = 0.35$, $w_p = 0.15$
- Cold-start fallback: $w_c = 0.85$, $w_p = 0.15$ (content-only)

---

## License

This project is for educational and portfolio purposes.

Dataset: [MovieLens 20M](https://grouplens.org/datasets/movielens/20m/) by GroupLens Research.  
Metadata: [TMDB API](https://www.themoviedb.org/) — This product uses the TMDB API but is not endorsed or certified by TMDB.

---

<div align="center">

**Built by [Priyansh Agarwal](https://github.com/priyansh-agg)**

</div>
