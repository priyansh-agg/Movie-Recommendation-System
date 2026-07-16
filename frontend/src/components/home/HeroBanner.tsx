import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Star, Eye, Bookmark, Clock } from 'lucide-react';
import type { MovieRec } from '../../api/movies';
import Button from '../ui/Button';
import './HeroBanner.css';

interface HeroBannerProps {
  movie: MovieRec;
}

const stagger = {
  hidden: {},
  show: { transition: { staggerChildren: 0.15, delayChildren: 0.3 } },
};

const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  show: { opacity: 1, y: 0, transition: { duration: 0.6, ease: 'easeOut' } },
};

export default function HeroBanner({ movie }: HeroBannerProps) {
  const navigate = useNavigate();
  const meta = movie.metadata;
  const backdropUrl = meta?.poster_path
    ? `https://image.tmdb.org/t/p/w1280${meta.poster_path}`
    : null;
  const genres = meta?.genres
    ?.split(',')
    .map((g) => g.trim())
    .filter(Boolean)
    .slice(0, 4) ?? [];
  const year = meta?.release_year ||
    (meta?.release_date ? new Date(meta.release_date).getFullYear() : null);
  const runtime = meta?.runtime ? formatRuntime(meta.runtime) : null;

  return (
    <div className="hero">
      {/* Background */}
      <div className="hero__backdrop">
        {backdropUrl && <img src={backdropUrl} alt="" />}
        <div className="hero__overlay-bottom" />
        <div className="hero__overlay-left" />
      </div>

      {/* Content */}
      <motion.div
        className="hero__content"
        variants={stagger}
        initial="hidden"
        animate="show"
      >
        <motion.h1 className="hero__title" variants={fadeUp}>
          {movie.title}
        </motion.h1>

        <motion.div className="hero__meta" variants={fadeUp}>
          {meta?.vote_average && meta.vote_average > 0 && (
            <span className="hero__rating">
              <Star size={16} fill="var(--rating-gold)" stroke="var(--rating-gold)" />
              {meta.vote_average.toFixed(1)}
            </span>
          )}
          {year && <span className="hero__year">{year}</span>}
          {runtime && (
            <span className="hero__runtime">
              <Clock size={14} /> {runtime}
            </span>
          )}
          {genres.map((g) => (
            <span key={g} className="hero__genre-pill">{g}</span>
          ))}
        </motion.div>

        {meta?.tagline && (
          <motion.p className="hero__tagline" variants={fadeUp}>
            {meta.tagline}
          </motion.p>
        )}

        {meta?.overview && (
          <motion.p className="hero__overview" variants={fadeUp}>
            {meta.overview}
          </motion.p>
        )}

        <motion.div className="hero__buttons" variants={fadeUp}>
          <Button
            variant="primary"
            size="lg"
            icon={<Eye size={18} />}
            onClick={() => navigate(`/movie/${movie.tmdbId}`)}
          >
            View Details
          </Button>
          <Button
            variant="secondary"
            size="lg"
            icon={<Bookmark size={18} />}
          >
            Watchlist
          </Button>
        </motion.div>
      </motion.div>
    </div>
  );
}

function formatRuntime(minutes: number): string {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return h > 0 ? `${h}h ${m}m` : `${m}m`;
}
