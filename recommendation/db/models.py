"""
SQLAlchemy ORM models — maps to the PostgreSQL schema.

Tables:
    users, user_preferences, user_ratings, user_likes,
    user_watchlist, user_watch_history, user_interactions
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(50), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    movielens_user_id = Column(Integer, nullable=True)
    onboarded = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    preferences = relationship(
        "UserPreferencesModel", back_populates="user", uselist=False,
        cascade="all, delete-orphan",
    )
    ratings = relationship(
        "UserRatingModel", back_populates="user", cascade="all, delete-orphan"
    )
    likes = relationship(
        "UserLikeModel", back_populates="user", cascade="all, delete-orphan"
    )
    watchlist = relationship(
        "UserWatchlistModel", back_populates="user", cascade="all, delete-orphan"
    )
    watch_history = relationship(
        "UserWatchHistoryModel", back_populates="user",
        cascade="all, delete-orphan", order_by="UserWatchHistoryModel.watched_at.desc()",
    )
    interactions = relationship(
        "UserInteractionModel", back_populates="user",
        cascade="all, delete-orphan", order_by="UserInteractionModel.created_at.desc()",
    )


class UserPreferencesModel(Base):
    __tablename__ = "user_preferences"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    favorite_genres = Column(ARRAY(Text), default=[])
    favorite_movies = Column(ARRAY(Integer), default=[])
    disliked_genres = Column(ARRAY(Text), default=[])

    user = relationship("UserModel", back_populates="preferences")


class UserRatingModel(Base):
    __tablename__ = "user_ratings"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    tmdb_id = Column(Integer, primary_key=True)
    rating = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("UserModel", back_populates="ratings")


class UserLikeModel(Base):
    __tablename__ = "user_likes"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    tmdb_id = Column(Integer, primary_key=True)
    is_like = Column(Boolean, nullable=False)  # True=like, False=dislike
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("UserModel", back_populates="likes")


class UserWatchlistModel(Base):
    __tablename__ = "user_watchlist"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    tmdb_id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("UserModel", back_populates="watchlist")


class UserWatchHistoryModel(Base):
    __tablename__ = "user_watch_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    tmdb_id = Column(Integer, nullable=False)
    watched_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("UserModel", back_populates="watch_history")


class UserInteractionModel(Base):
    __tablename__ = "user_interactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    tmdb_id = Column(Integer, nullable=False)
    interaction_type = Column(String(20), nullable=False)
    value = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("UserModel", back_populates="interactions")
