import { useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import type { MovieRec } from '../../api/movies';
import MovieCard from './MovieCard';
import './MovieRow.css';

interface MovieRowProps {
  title: string;
  movies: MovieRec[];
  loading?: boolean;
}

export default function MovieRow({ title, movies, loading }: MovieRowProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const sectionRef = useRef<HTMLDivElement>(null);
  const isInView = useInView(sectionRef, { once: true, margin: '-60px' });

  const scroll = (direction: 'left' | 'right') => {
    if (!scrollRef.current) return;
    const amount = 4 * (180 + 16); // 4 cards
    scrollRef.current.scrollBy({
      left: direction === 'right' ? amount : -amount,
      behavior: 'smooth',
    });
  };

  if (!loading && movies.length === 0) return null;

  return (
    <motion.section
      ref={sectionRef}
      className="movie-row"
      initial={{ opacity: 0, x: 40 }}
      animate={isInView ? { opacity: 1, x: 0 } : {}}
      transition={{ duration: 0.5, ease: 'easeOut' }}
    >
      <h2 className="movie-row__title">{title}</h2>

      <div className="movie-row__container">
        <button
          className="movie-row__arrow movie-row__arrow--left"
          onClick={() => scroll('left')}
        >
          <ChevronLeft size={20} />
        </button>

        <div className="movie-row__scroll" ref={scrollRef}>
          {loading
            ? Array.from({ length: 7 }).map((_, i) => (
                <div key={i} className="movie-row__skeleton" />
              ))
            : movies.map((movie) => (
                <MovieCard key={movie.tmdbId} movie={movie} />
              ))}
        </div>

        <button
          className="movie-row__arrow movie-row__arrow--right"
          onClick={() => scroll('right')}
        >
          <ChevronRight size={20} />
        </button>
      </div>
    </motion.section>
  );
}
