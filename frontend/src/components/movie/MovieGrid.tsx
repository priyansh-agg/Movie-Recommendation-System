import { motion } from 'framer-motion';
import { Film } from 'lucide-react';
import type { MovieRec } from '../../api/movies';
import MovieCard from './MovieCard';
import './MovieGrid.css';

interface MovieGridProps {
  movies: MovieRec[];
  loading?: boolean;
  emptyMessage?: string;
}

const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.04 } },
};

const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { duration: 0.35 } },
};

export default function MovieGrid({
  movies,
  loading,
  emptyMessage = 'No movies found',
}: MovieGridProps) {
  if (loading) {
    return (
      <div className="movie-grid">
        {Array.from({ length: 12 }).map((_, i) => (
          <div key={i} className="movie-grid__skeleton" />
        ))}
      </div>
    );
  }

  if (movies.length === 0) {
    return (
      <div className="movie-grid__empty">
        <Film size={48} />
        <p>{emptyMessage}</p>
      </div>
    );
  }

  return (
    <motion.div
      className="movie-grid"
      variants={container}
      initial="hidden"
      animate="show"
    >
      {movies.map((movie) => (
        <motion.div key={movie.tmdbId} variants={item}>
          <MovieCard movie={movie} />
        </motion.div>
      ))}
    </motion.div>
  );
}
