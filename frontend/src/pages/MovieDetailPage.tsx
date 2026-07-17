import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import {
  Star, Clock, Globe, Heart, Bookmark, Eye, ArrowLeft,
} from 'lucide-react';
import { getSimilarMovies, searchMovies } from '../api/movies';
import { rateMovie, likeMovie, toggleWatchlist, markWatched } from '../api/user';
import type { MovieRec } from '../api/movies';
import PageTransition from '../components/layout/PageTransition';
import MovieRow from '../components/movie/MovieRow';
import RatingStars from '../components/movie/RatingStars';
import Button from '../components/ui/Button';
import Loader from '../components/ui/Loader';
import { useAuthStore } from '../stores/authStore';
import { useToast } from '../components/ui/Toast';
import './MovieDetailPage.css';

export default function MovieDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const tmdbId = parseInt(id || '0', 10);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const user = useAuthStore((s) => s.user);
  const fetchProfile = useAuthStore((s) => s.fetchProfile);
  const { showToast } = useToast();
  const queryClient = useQueryClient();
  const watchlistActionRef = useRef<'add' | 'remove'>('add');

  // First: try to find movie in cache
  const cachedMovie = findMovieInCache(queryClient, tmdbId);

  // If not in cache, we need to fetch it via search + similar
  const { data: fetchedMovie, isLoading: loadingMovie } = useQuery({
    queryKey: ['movie-detail', tmdbId],
    queryFn: async (): Promise<MovieRec | null> => {
      // Search by tmdbId to get the title
      const searchData = await searchMovies(String(tmdbId), 5);
      const match = searchData.results.find((r) => r.tmdbId === tmdbId);
      if (!match) return null;

      // Use similar movies to get full metadata
      const similarData = await getSimilarMovies([match.title], 1);
      // The API might return the source movie with metadata
      // Build a stub with what we have
      return {
        movieId: null,
        tmdbId: match.tmdbId,
        title: match.title,
        poster: null,
        scores: { content: null, collaborative: null, popularity: null, hybrid: null },
        metadata: similarData.recommendations[0]?.metadata || null,
        source: 'detail',
      };
    },
    staleTime: 10 * 60 * 1000,
    enabled: tmdbId > 0 && !cachedMovie,
  });

  const movie = cachedMovie || fetchedMovie || null;

  // Fetch similar movies (needs movie title)
  const { data: similarData, isLoading: loadingSimilar } = useQuery({
    queryKey: ['similar', tmdbId],
    queryFn: async () => {
      const movieTitle = movie?.title;
      if (!movieTitle) {
        // Try search
        const searchData = await searchMovies(String(tmdbId), 1);
        const title = searchData.results[0]?.title;
        if (!title) return { recommendations: [] };
        return getSimilarMovies([title], 12);
      }
      return getSimilarMovies([movieTitle], 12);
    },
    staleTime: 5 * 60 * 1000,
    enabled: tmdbId > 0 && !!movie,
  });

  useEffect(() => {
    document.title = movie?.title
      ? `${movie.title} — CINEMATIC`
      : 'Movie Details — CINEMATIC';
    window.scrollTo(0, 0);
  }, [movie?.title]);

  // Mutations
  const rateMut = useMutation({
    mutationFn: (rating: number) => rateMovie(tmdbId, rating),
    onSuccess: () => {
      showToast('Rating saved', 'success');
      fetchProfile();
    },
    onError: () => showToast('Please login to rate movies', 'error'),
  });

  const likeMut = useMutation({
    mutationFn: () => likeMovie(tmdbId),
    onSuccess: () => {
      showToast('Added to liked movies', 'success');
      fetchProfile();
    },
    onError: () => showToast('Please login to like movies', 'error'),
  });

  const watchlistMut = useMutation({
    mutationFn: () => {
      const inWl = user?.watchlist?.includes(tmdbId);
      const action = inWl ? 'remove' : 'add';
      watchlistActionRef.current = action; // capture before async
      return toggleWatchlist(tmdbId, action);
    },
    onSuccess: () => {
      showToast(
        watchlistActionRef.current === 'remove' ? 'Removed from watchlist' : 'Added to watchlist',
        'success',
      );
      fetchProfile();
    },
    onError: () => showToast('Please login first', 'error'),
  });

  const watchedMut = useMutation({
    mutationFn: () => markWatched(tmdbId),
    onSuccess: () => {
      showToast('Marked as watched', 'success');
      fetchProfile();
    },
    onError: () => showToast('Please login first', 'error'),
  });

  // Loading state
  if (!movie && loadingMovie) {
    return <Loader fullPage />;
  }

  // Not found
  if (!movie && !loadingMovie) {
    return (
      <PageTransition>
        <div className="movie-detail__not-found">
          <p>Movie not found</p>
          <Button variant="secondary" onClick={() => navigate(-1)} icon={<ArrowLeft size={16} />}>
            Go Back
          </Button>
        </div>
      </PageTransition>
    );
  }

  if (!movie) return null;

  const meta = movie.metadata;
  const posterUrl = meta?.poster_path
    ? `https://image.tmdb.org/t/p/w780${meta.poster_path}`
    : movie.poster;
  const backdropUrl = meta?.poster_path
    ? `https://image.tmdb.org/t/p/w1280${meta.poster_path}`
    : null;
  const genres = meta?.genres?.split(',').map((g: string) => g.trim()).filter(Boolean) || [];
  const year = meta?.release_year || (meta?.release_date ? new Date(meta.release_date).getFullYear() : null);
  const runtime = meta?.runtime ? formatRuntime(meta.runtime) : null;
  const isLiked = user?.liked?.includes(tmdbId);
  const inWatchlist = user?.watchlist?.includes(tmdbId);
  const currentRating = user?.ratings?.[String(tmdbId)] || 0;

  const stagger = {
    hidden: {},
    show: { transition: { staggerChildren: 0.12 } },
  };
  const fadeUp = {
    hidden: { opacity: 0, y: 25 },
    show: { opacity: 1, y: 0, transition: { duration: 0.5 } },
  };

  return (
    <PageTransition>
      <div className="movie-detail">
        {/* Backdrop */}
        <div className="movie-detail__backdrop">
          {backdropUrl && (
            <img src={backdropUrl} alt="" className="movie-detail__backdrop-img" />
          )}
          <div className="movie-detail__backdrop-overlay" />
          <div className="movie-detail__backdrop-overlay-left" />
        </div>

        {/* Content */}
        <motion.div
          className="movie-detail__content"
          variants={stagger}
          initial="hidden"
          animate="show"
        >
          <button className="movie-detail__back" onClick={() => navigate(-1)}>
            <ArrowLeft size={18} />
            <span>Back</span>
          </button>

          <div className="movie-detail__layout">
            {/* Poster */}
            <motion.div className="movie-detail__poster" variants={fadeUp}>
              {posterUrl ? (
                <img src={posterUrl} alt={movie.title} />
              ) : (
                <div className="movie-detail__poster-placeholder">
                  <span>{movie.title}</span>
                </div>
              )}
            </motion.div>

            {/* Info */}
            <div className="movie-detail__info">
              <motion.h1 className="movie-detail__title" variants={fadeUp}>
                {movie.title}
                {year && <span className="movie-detail__year"> ({year})</span>}
              </motion.h1>

              <motion.div className="movie-detail__meta-row" variants={fadeUp}>
                {meta?.vote_average && meta.vote_average > 0 && (
                  <span className="movie-detail__rating">
                    <Star size={16} fill="var(--rating-gold)" stroke="var(--rating-gold)" />
                    {meta.vote_average.toFixed(1)}
                    {meta?.vote_count && (
                      <span className="movie-detail__votes">
                        ({meta.vote_count.toLocaleString()} votes)
                      </span>
                    )}
                  </span>
                )}
                {runtime && (
                  <span className="movie-detail__runtime">
                    <Clock size={14} /> {runtime}
                  </span>
                )}
                {meta?.original_language && (
                  <span className="movie-detail__lang">
                    <Globe size={14} /> {meta.original_language.toUpperCase()}
                  </span>
                )}
              </motion.div>

              {genres.length > 0 && (
                <motion.div className="movie-detail__genres" variants={fadeUp}>
                  {genres.map((g: string) => (
                    <span key={g} className="movie-detail__genre-pill">{g}</span>
                  ))}
                </motion.div>
              )}

              {meta?.tagline && (
                <motion.p className="movie-detail__tagline" variants={fadeUp}>
                  "{meta.tagline}"
                </motion.p>
              )}

              {meta?.overview && (
                <motion.div className="movie-detail__overview" variants={fadeUp}>
                  <h3>Overview</h3>
                  <p>{meta.overview}</p>
                </motion.div>
              )}

              {/* Actions */}
              {isAuthenticated && (
                <motion.div className="movie-detail__actions" variants={fadeUp}>
                  <div className="movie-detail__rate">
                    <span className="movie-detail__rate-label">Your Rating</span>
                    <RatingStars
                      value={currentRating}
                      onChange={(r) => rateMut.mutate(r)}
                      size="lg"
                    />
                  </div>
                  <div className="movie-detail__buttons">
                    <Button
                      variant={isLiked ? 'primary' : 'secondary'}
                      icon={<Heart size={16} fill={isLiked ? 'currentColor' : 'none'} />}
                      onClick={() => likeMut.mutate()}
                      loading={likeMut.isPending}
                    >
                      {isLiked ? 'Liked' : 'Like'}
                    </Button>
                    <Button
                      variant={inWatchlist ? 'primary' : 'secondary'}
                      icon={<Bookmark size={16} fill={inWatchlist ? 'currentColor' : 'none'} />}
                      onClick={() => watchlistMut.mutate()}
                      loading={watchlistMut.isPending}
                    >
                      {inWatchlist ? 'In Watchlist' : 'Watchlist'}
                    </Button>
                    <Button
                      variant="ghost"
                      icon={<Eye size={16} />}
                      onClick={() => watchedMut.mutate()}
                      loading={watchedMut.isPending}
                    >
                      Watched
                    </Button>
                  </div>
                </motion.div>
              )}
            </div>
          </div>
        </motion.div>

        {/* Similar Movies */}
        <div className="movie-detail__similar">
          <MovieRow
            title="Similar Movies"
            movies={similarData?.recommendations ?? []}
            loading={loadingSimilar}
          />
        </div>
      </div>
    </PageTransition>
  );
}

function formatRuntime(minutes: number): string {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return h > 0 ? `${h}h ${m}m` : `${m}m`;
}

function findMovieInCache(queryClient: any, tmdbId: number): MovieRec | null {
  // Search through homepage cache
  const homepage = queryClient.getQueryData<{ sections: { movies: MovieRec[] }[] }>(['homepage']);
  if (homepage) {
    for (const section of homepage.sections) {
      const found = section.movies.find((m) => m.tmdbId === tmdbId);
      if (found) return found;
    }
  }
  // Search through similar movie caches
  const queries = queryClient.getQueriesData<{ recommendations: MovieRec[] }>({ queryKey: ['similar'] });
  for (const [, data] of queries) {
    if (data?.recommendations) {
      const found = data.recommendations.find((m) => m.tmdbId === tmdbId);
      if (found) return found;
    }
  }
  return null;
}
