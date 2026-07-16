import { useEffect } from 'react';
import { Bookmark } from 'lucide-react';
import { useAuthStore } from '../stores/authStore';
import PageTransition from '../components/layout/PageTransition';
import MovieGrid from '../components/movie/MovieGrid';
import type { MovieRec } from '../api/movies';
import './WatchlistPage.css';

export default function WatchlistPage() {
  const user = useAuthStore((s) => s.user);
  const fetchProfile = useAuthStore((s) => s.fetchProfile);

  useEffect(() => {
    document.title = 'My Watchlist — CINEMATIC';
    fetchProfile();
  }, [fetchProfile]);

  // Build MovieRec stubs from watchlist tmdb IDs
  const movies: MovieRec[] = (user?.watchlist ?? []).map((tmdbId) => ({
    movieId: null,
    tmdbId,
    title: `Movie #${tmdbId}`,
    poster: null,
    scores: { content: null, collaborative: null, popularity: null, hybrid: null },
    metadata: null,
    source: 'watchlist',
  }));

  return (
    <PageTransition>
      <div className="watchlist-page">
        <div className="watchlist-page__header">
          <Bookmark size={28} />
          <h1>My Watchlist</h1>
          <span className="watchlist-page__count">{movies.length} movies</span>
        </div>

        <MovieGrid
          movies={movies}
          emptyMessage="Your watchlist is empty. Browse movies and add some!"
        />
      </div>
    </PageTransition>
  );
}
