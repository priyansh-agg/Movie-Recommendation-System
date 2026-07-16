import client from './client';

/* ── Types ──────────────────────────────────────────────────────────── */

export interface UserPreferences {
  favorite_genres: string[];
  favorite_movies: number[];
  disliked_genres: string[];
}

export interface UserProfile {
  id: number;
  email: string;
  username: string;
  onboarded: boolean;
  preferences: UserPreferences;
  watch_history: number[];
  watchlist: number[];
  ratings: Record<string, number>;
  ratings_count: number;
  liked: number[];
  liked_count: number;
  disliked: number[];
}

/* ── API Functions ──────────────────────────────────────────────────── */

export async function getProfile(): Promise<UserProfile> {
  const { data } = await client.get<UserProfile>('/users/me');
  return data;
}

export async function updateProfile(
  update: Partial<{ username: string; preferences: Partial<UserPreferences> }>,
): Promise<UserProfile> {
  const { data } = await client.put<UserProfile>('/users/me', update);
  return data;
}

export async function rateMovie(
  tmdbId: number,
  rating: number,
): Promise<{ message: string }> {
  const { data } = await client.post('/feedback/rate', {
    tmdb_id: tmdbId,
    rating,
  });
  return data;
}

export async function likeMovie(tmdbId: number): Promise<{ message: string }> {
  const { data } = await client.post('/feedback/like', { tmdb_id: tmdbId });
  return data;
}

export async function dislikeMovie(
  tmdbId: number,
): Promise<{ message: string }> {
  const { data } = await client.post('/feedback/dislike', {
    tmdb_id: tmdbId,
  });
  return data;
}

export async function toggleWatchlist(
  tmdbId: number,
  action: 'add' | 'remove',
): Promise<{ message: string }> {
  const { data } = await client.post('/feedback/watchlist', {
    tmdb_id: tmdbId,
    action,
  });
  return data;
}

export async function markWatched(
  tmdbId: number,
): Promise<{ message: string }> {
  const { data } = await client.post('/feedback/watched', {
    tmdb_id: tmdbId,
  });
  return data;
}
