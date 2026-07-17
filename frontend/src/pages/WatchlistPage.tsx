import { useEffect, useState } from 'react';
import { Bookmark } from 'lucide-react';
import { useAuthStore } from '../stores/authStore';
import PageTransition from '../components/layout/PageTransition';
import MovieGrid from '../components/movie/MovieGrid';
import Loader from '../components/ui/Loader';
import type { MovieRec } from '../api/movies';
import client from '../api/client';
import './WatchlistPage.css';

interface MovieDetail {
  tmdbId: number;
  title: string;
  poster_path?: string;
  vote_average?: number;
  genres?: string;
  release_year?: number;
  overview?: string;
}

export default function WatchlistPage() {
  const user = useAuthStore((s) => s.user);
  const fetchProfile = useAuthStore((s) => s.fetchProfile);
  const [movies, setMovies] = useState<MovieRec[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    document.title = 'My Watchlist — CINEMATIC';
    fetchProfile();
  }, [fetchProfile]);

  // Fetch real movie data for watchlist items
  useEffect(() => {
    const tmdbIds = user?.watchlist ?? [];
    if (tmdbIds.length === 0) {
      setMovies([]);
      setLoading(false);
      return;
    }

    let cancelled = false;

    async function fetchWatchlistMovies() {
      setLoading(true);
      try {
        // Try batch endpoint first, fall back to search
        const results: MovieRec[] = [];
        for (const tmdbId of tmdbIds) {
          try {
            const { data } = await client.get(`/search`, {
              params: { q: String(tmdbId), max_results: 1 },
            });
            const match = data.results?.find(
              (r: { tmdbId: number }) => r.tmdbId === tmdbId
            );
            if (match) {
              // Get poster via similar endpoint
              const { data: simData } = await client.get(
                '/recommendations/similar',
                { params: { movies: match.title, top_n: 1 } }
              );
              const simMovie = simData.recommendations?.[0];
              results.push({
                movieId: null,
                tmdbId,
                title: match.title,
                poster: simMovie?.poster ?? null,
                scores: {
                  content: null,
                  collaborative: null,
                  popularity: null,
                  hybrid: null,
                },
                metadata: simMovie?.metadata ?? null,
                source: 'watchlist',
              });
            } else {
              results.push({
                movieId: null,
                tmdbId,
                title: `Movie #${tmdbId}`,
                poster: null,
                scores: {
                  content: null,
                  collaborative: null,
                  popularity: null,
                  hybrid: null,
                },
                metadata: null,
                source: 'watchlist',
              });
            }
          } catch {
            results.push({
              movieId: null,
              tmdbId,
              title: `Movie #${tmdbId}`,
              poster: null,
              scores: {
                content: null,
                collaborative: null,
                popularity: null,
                hybrid: null,
              },
              metadata: null,
              source: 'watchlist',
            });
          }
        }
        if (!cancelled) {
          setMovies(results);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    fetchWatchlistMovies();
    return () => { cancelled = true; };
  }, [user?.watchlist]);

  return (
    <PageTransition>
      <div className="watchlist-page">
        <div className="watchlist-page__header">
          <Bookmark size={28} />
          <h1>My Watchlist</h1>
          <span className="watchlist-page__count">{movies.length} movies</span>
        </div>

        {loading ? (
          <Loader size="lg" />
        ) : (
          <MovieGrid
            movies={movies}
            emptyMessage="Your watchlist is empty. Browse movies and add some!"
          />
        )}
      </div>
    </PageTransition>
  );
}
