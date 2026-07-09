"""
PostgreSQL implementation of UserRepository.

Drop-in replacement for ``InMemoryUserRepository``.  Change one
import in ``api/dependencies.py`` to switch storage backends.
"""

import time
from datetime import datetime

from sqlalchemy.orm import Session

from recommendation.user.repository import UserRepository
from recommendation.user.schemas import (
    Interaction,
    UserPreferences,
    UserProfile,
)
from recommendation.db.models import (
    UserModel,
    UserPreferencesModel,
    UserRatingModel,
    UserLikeModel,
    UserWatchlistModel,
    UserWatchHistoryModel,
    UserInteractionModel,
)
from recommendation.db.session import SessionLocal


class PostgresUserRepository(UserRepository):
    """
    PostgreSQL-backed user repository.

    Each method opens its own session and commits.  This is simpler
    than passing sessions around and works fine for the current
    request-per-call pattern.
    """

    # ── Helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _to_profile(user: UserModel) -> UserProfile:
        """Convert ORM model → domain schema."""
        prefs = UserPreferences(
            favorite_genres=user.preferences.favorite_genres or []
                if user.preferences else [],
            favorite_movies=user.preferences.favorite_movies or []
                if user.preferences else [],
            disliked_genres=user.preferences.disliked_genres or []
                if user.preferences else [],
        )

        ratings_dict = {r.tmdb_id: r.rating for r in user.ratings}

        liked = [lk.tmdb_id for lk in user.likes if lk.is_like]
        disliked = [lk.tmdb_id for lk in user.likes if not lk.is_like]

        watchlist = [w.tmdb_id for w in user.watchlist]

        watch_history = [wh.tmdb_id for wh in user.watch_history]

        interactions = [
            Interaction(
                tmdb_id=i.tmdb_id,
                interaction_type=i.interaction_type,
                value=i.value,
                timestamp=i.created_at.timestamp() if i.created_at else time.time(),
            )
            for i in user.interactions
        ]

        return UserProfile(
            id=user.id,
            email=user.email,
            username=user.username,
            hashed_password=user.hashed_password,
            movielens_user_id=user.movielens_user_id,
            preferences=prefs,
            watch_history=watch_history,
            watchlist=watchlist,
            ratings=ratings_dict,
            liked=liked,
            disliked=disliked,
            interactions=interactions,
            onboarded=user.onboarded or False,
            created_at=user.created_at.timestamp() if user.created_at else time.time(),
        )

    # ── CRUD ────────────────────────────────────────────────────────

    def create(self, email: str, username: str, hashed_password: str) -> UserProfile:
        with SessionLocal() as db:
            # Check duplicate
            existing = db.query(UserModel).filter(UserModel.email == email).first()
            if existing:
                raise ValueError(f"Email '{email}' is already registered")

            user = UserModel(
                email=email,
                username=username,
                hashed_password=hashed_password,
                created_at=datetime.utcnow(),
            )
            db.add(user)
            db.flush()

            # Create empty preferences row
            prefs = UserPreferencesModel(
                user_id=user.id,
                favorite_genres=[],
                favorite_movies=[],
                disliked_genres=[],
            )
            db.add(prefs)
            db.commit()
            db.refresh(user)

            return self._to_profile(user)

    def get_by_id(self, user_id: int) -> UserProfile | None:
        with SessionLocal() as db:
            user = db.query(UserModel).filter(UserModel.id == user_id).first()
            if user is None:
                return None
            return self._to_profile(user)

    def get_by_email(self, email: str) -> UserProfile | None:
        with SessionLocal() as db:
            user = db.query(UserModel).filter(UserModel.email == email).first()
            if user is None:
                return None
            return self._to_profile(user)

    def update(self, profile: UserProfile) -> UserProfile:
        with SessionLocal() as db:
            user = db.query(UserModel).filter(UserModel.id == profile.id).first()
            if user is None:
                raise ValueError("User not found")

            # Update basic fields
            user.username = profile.username
            user.onboarded = profile.onboarded
            user.movielens_user_id = profile.movielens_user_id

            # Update preferences
            if user.preferences is None:
                user.preferences = UserPreferencesModel(user_id=user.id)
            user.preferences.favorite_genres = profile.preferences.favorite_genres
            user.preferences.favorite_movies = profile.preferences.favorite_movies
            user.preferences.disliked_genres = profile.preferences.disliked_genres

            # Sync ratings (upsert)
            existing_ratings = {r.tmdb_id: r for r in user.ratings}
            for tmdb_id, rating_val in profile.ratings.items():
                if tmdb_id in existing_ratings:
                    existing_ratings[tmdb_id].rating = rating_val
                else:
                    db.add(UserRatingModel(
                        user_id=profile.id, tmdb_id=tmdb_id, rating=rating_val
                    ))

            # Sync likes/dislikes
            existing_likes = {lk.tmdb_id: lk for lk in user.likes}
            all_like_ids = set(profile.liked + profile.disliked)

            for tmdb_id in profile.liked:
                if tmdb_id in existing_likes:
                    existing_likes[tmdb_id].is_like = True
                else:
                    db.add(UserLikeModel(
                        user_id=profile.id, tmdb_id=tmdb_id, is_like=True
                    ))

            for tmdb_id in profile.disliked:
                if tmdb_id in existing_likes:
                    existing_likes[tmdb_id].is_like = False
                else:
                    db.add(UserLikeModel(
                        user_id=profile.id, tmdb_id=tmdb_id, is_like=False
                    ))

            # Remove stale likes
            for tmdb_id, lk in existing_likes.items():
                if tmdb_id not in all_like_ids:
                    db.delete(lk)

            # Sync watchlist
            existing_wl = {w.tmdb_id: w for w in user.watchlist}
            new_wl = set(profile.watchlist)

            for tmdb_id in new_wl - set(existing_wl.keys()):
                db.add(UserWatchlistModel(
                    user_id=profile.id, tmdb_id=tmdb_id
                ))
            for tmdb_id in set(existing_wl.keys()) - new_wl:
                db.delete(existing_wl[tmdb_id])

            # Sync watch history (append new entries)
            existing_wh_ids = {wh.tmdb_id for wh in user.watch_history}
            for tmdb_id in profile.watch_history:
                if tmdb_id not in existing_wh_ids:
                    db.add(UserWatchHistoryModel(
                        user_id=profile.id, tmdb_id=tmdb_id
                    ))
                    existing_wh_ids.add(tmdb_id)

            # Append new interactions
            existing_count = len(user.interactions)
            new_interactions = profile.interactions[
                :len(profile.interactions) - existing_count
            ] if len(profile.interactions) > existing_count else []

            for interaction in new_interactions:
                db.add(UserInteractionModel(
                    user_id=profile.id,
                    tmdb_id=interaction.tmdb_id,
                    interaction_type=interaction.interaction_type,
                    value=interaction.value,
                ))

            db.commit()
            db.refresh(user)
            return self._to_profile(user)

    def exists_email(self, email: str) -> bool:
        with SessionLocal() as db:
            return db.query(UserModel).filter(UserModel.email == email).count() > 0
