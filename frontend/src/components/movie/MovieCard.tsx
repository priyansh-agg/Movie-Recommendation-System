import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Star, Heart, Bookmark } from 'lucide-react';
import type { MovieRec } from '../../api/movies';
import './MovieCard.css';

interface MovieCardProps {
  movie: MovieRec;
}

function getPosterUrl(movie: MovieRec): string | null {
  if (movie.poster?.startsWith('http')) return movie.poster;
  if (movie.metadata?.poster_path)
    return `https://image.tmdb.org/t/p/w342${movie.metadata.poster_path}`;
  return null;
}

export default function MovieCard({ movie }: MovieCardProps) {
  const [imgLoaded, setImgLoaded] = useState(false);
  const navigate = useNavigate();
  const posterUrl = getPosterUrl(movie);
  const genres = movie.metadata?.genres
    ?.split(',')
    .map((g) => g.trim())
    .filter(Boolean)
    .slice(0, 2) ?? [];
  const voteAvg = movie.metadata?.vote_average ?? 0;
  const year = movie.metadata?.release_year ||
    (movie.metadata?.release_date
      ? new Date(movie.metadata.release_date).getFullYear()
      : null);

  return (
    <motion.div
      className="movie-card"
      whileHover={{ scale: 1.05 }}
      transition={{ type: 'spring', stiffness: 300, damping: 20 }}
      onClick={() => navigate(`/movie/${movie.tmdbId}`)}
    >
      <div className="movie-card__poster">
        {posterUrl ? (
          <>
            {!imgLoaded && <div className="movie-card__skeleton" />}
            <img
              src={posterUrl}
              alt={movie.title}
              loading="lazy"
              onLoad={() => setImgLoaded(true)}
              style={{ opacity: imgLoaded ? 1 : 0 }}
            />
          </>
        ) : (
          <div className="movie-card__placeholder">
            <span>{movie.title}</span>
          </div>
        )}

        {/* Rating badge */}
        {voteAvg > 0 && (
          <div className="movie-card__rating">
            <Star size={11} fill="var(--rating-gold)" stroke="var(--rating-gold)" />
            <span>{voteAvg.toFixed(1)}</span>
          </div>
        )}

        {/* Hover overlay */}
        <div className="movie-card__overlay">
          {genres.length > 0 && (
            <span className="movie-card__genres">
              {genres.join(' / ')}
            </span>
          )}
          <div className="movie-card__actions">
            <button className="movie-card__action-btn" onClick={(e) => e.stopPropagation()}>
              <Heart size={14} />
            </button>
            <button className="movie-card__action-btn" onClick={(e) => e.stopPropagation()}>
              <Bookmark size={14} />
            </button>
          </div>
        </div>
      </div>

      <div className="movie-card__info">
        <h3 className="movie-card__title">{movie.title}</h3>
        {year && <span className="movie-card__year">{year}</span>}
      </div>
    </motion.div>
  );
}
