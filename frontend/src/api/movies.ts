import client from './client';

/* ── Types ──────────────────────────────────────────────────────────── */

export interface MovieScores {
  content: number | null;
  collaborative: number | null;
  popularity: number | null;
  hybrid: number | null;
}

export interface MovieMetadata {
  title?: string;
  overview?: string;
  genres?: string;
  keywords?: string;
  vote_average?: number;
  vote_count?: number;
  popularity?: number;
  release_date?: string;
  release_year?: number;
  runtime?: number;
  original_language?: string;
  poster_path?: string;
  tagline?: string;
}

export interface MovieRec {
  movieId: number | null;
  tmdbId: number;
  title: string;
  poster: string | null;
  scores: MovieScores;
  metadata: MovieMetadata | null;
  explanation?: {
    engine: string;
    source_movie: string;
    reasons: string[];
  };
  source?: string;
}

export interface SearchResult {
  title: string;
  tmdbId: number;
}

export interface HomepageSection {
  title: string;
  movies: MovieRec[];
}

/* ── API Functions ──────────────────────────────────────────────────── */

export async function searchMovies(
  query: string,
  maxResults = 10,
): Promise<{ results: SearchResult[]; query: string; count: number }> {
  const { data } = await client.get('/search', {
    params: { q: query, max_results: maxResults },
  });
  return data;
}

export async function getSimilarMovies(
  movies: string[],
  topN = 10,
): Promise<{ recommendations: MovieRec[] }> {
  const { data } = await client.get('/recommendations/similar', {
    params: { movies: movies[0], top_n: topN },
  });
  return data;
}

export async function getHomepage(): Promise<{ sections: HomepageSection[] }> {
  const { data } = await client.get('/recommendations/homepage');
  return data;
}
