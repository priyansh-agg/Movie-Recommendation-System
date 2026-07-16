import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Check } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { getHomepage } from '../api/movies';
import type { MovieRec } from '../api/movies';
import PageTransition from '../components/layout/PageTransition';
import Button from '../components/ui/Button';
import { useToast } from '../components/ui/Toast';
import './OnboardingPage.css';

export default function OnboardingPage() {
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const navigate = useNavigate();
  const { showToast } = useToast();

  useEffect(() => {
    document.title = 'Get Started — CINEMATIC';
  }, []);

  // Get movies from homepage to use as onboarding choices
  const { data, isLoading } = useQuery({
    queryKey: ['homepage'],
    queryFn: getHomepage,
    staleTime: 5 * 60 * 1000,
  });

  // Flatten sections and deduplicate
  const allMovies: MovieRec[] = [];
  const seenIds = new Set<number>();
  if (data?.sections) {
    for (const section of data.sections) {
      for (const movie of section.movies) {
        if (!seenIds.has(movie.tmdbId) && movie.metadata?.poster_path) {
          seenIds.add(movie.tmdbId);
          allMovies.push(movie);
        }
      }
    }
  }

  const toggleSelect = useCallback((tmdbId: number) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(tmdbId)) next.delete(tmdbId);
      else next.add(tmdbId);
      return next;
    });
  }, []);

  const handleContinue = () => {
    if (selected.size < 5) {
      showToast('Please select at least 5 movies', 'error');
      return;
    }
    showToast('Preferences saved! Enjoy your recommendations.', 'success');
    navigate('/');
  };

  return (
    <PageTransition>
      <div className="onboarding">
        <div className="onboarding__header">
          <h1>Pick movies you enjoy</h1>
          <p>
            Select at least 5 movies to calibrate your taste. The more you pick,
            the better your recommendations.
          </p>
        </div>

        {isLoading ? (
          <div className="onboarding__grid">
            {Array.from({ length: 20 }).map((_, i) => (
              <div key={i} className="onboarding__skeleton" />
            ))}
          </div>
        ) : (
          <div className="onboarding__grid">
            <AnimatePresence>
              {allMovies.map((movie) => {
                const isSelected = selected.has(movie.tmdbId);
                const posterUrl = movie.metadata?.poster_path
                  ? `https://image.tmdb.org/t/p/w342${movie.metadata.poster_path}`
                  : null;

                return (
                  <motion.div
                    key={movie.tmdbId}
                    className={`onboarding__card ${isSelected ? 'onboarding__card--selected' : ''}`}
                    onClick={() => toggleSelect(movie.tmdbId)}
                    whileTap={{ scale: 0.95 }}
                    layout
                  >
                    {posterUrl && <img src={posterUrl} alt={movie.title} loading="lazy" />}
                    {isSelected && (
                      <motion.div
                        className="onboarding__check"
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ type: 'spring', stiffness: 500, damping: 20 }}
                      >
                        <Check size={24} />
                      </motion.div>
                    )}
                    <div className="onboarding__card-title">{movie.title}</div>
                  </motion.div>
                );
              })}
            </AnimatePresence>
          </div>
        )}

        {/* Sticky bottom bar */}
        <div className="onboarding__bottom">
          <span className="onboarding__count">
            {selected.size} selected
            {selected.size < 5 && ` — pick ${5 - selected.size} more`}
          </span>
          <Button
            variant="primary"
            size="lg"
            disabled={selected.size < 5}
            onClick={handleContinue}
          >
            Continue
          </Button>
        </div>
      </div>
    </PageTransition>
  );
}
