"""
User repository — abstract interface + in-memory implementation.

The abstract base class defines the contract that any storage backend
must satisfy.  ``InMemoryUserRepository`` is the development backend;
swap it for ``PostgresUserRepository`` in Phase 7 by changing one import
in ``api/dependencies.py``.
"""

import time
import threading
from abc import ABC, abstractmethod

from recommendation.user.schemas import UserProfile


class UserRepository(ABC):
    """Storage contract for user profiles."""

    @abstractmethod
    def create(self, email: str, username: str, hashed_password: str) -> UserProfile:
        ...

    @abstractmethod
    def get_by_id(self, user_id: int) -> UserProfile | None:
        ...

    @abstractmethod
    def get_by_email(self, email: str) -> UserProfile | None:
        ...

    @abstractmethod
    def update(self, profile: UserProfile) -> UserProfile:
        ...

    @abstractmethod
    def exists_email(self, email: str) -> bool:
        ...


class InMemoryUserRepository(UserRepository):
    """
    Thread-safe in-memory user store.

    Data lives for the lifetime of the process.  Good enough for
    development and testing; will be replaced by PostgreSQL.
    """

    def __init__(self):
        self._users: dict[int, UserProfile] = {}
        self._email_index: dict[str, int] = {}
        self._next_id: int = 1
        self._lock = threading.Lock()

    def create(self, email: str, username: str, hashed_password: str) -> UserProfile:
        with self._lock:
            if email in self._email_index:
                raise ValueError(f"Email '{email}' is already registered")

            user_id = self._next_id
            self._next_id += 1

            profile = UserProfile(
                id=user_id,
                email=email,
                username=username,
                hashed_password=hashed_password,
                created_at=time.time(),
            )
            self._users[user_id] = profile
            self._email_index[email] = user_id
            return profile

    def get_by_id(self, user_id: int) -> UserProfile | None:
        return self._users.get(user_id)

    def get_by_email(self, email: str) -> UserProfile | None:
        uid = self._email_index.get(email)
        return self._users.get(uid) if uid is not None else None

    def update(self, profile: UserProfile) -> UserProfile:
        with self._lock:
            self._users[profile.id] = profile
            return profile

    def exists_email(self, email: str) -> bool:
        return email in self._email_index
