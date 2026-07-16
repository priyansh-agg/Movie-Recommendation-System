import { useState, useEffect, useRef, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Search, Film } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { motion, AnimatePresence } from 'framer-motion';
import { searchMovies } from '../api/movies';
import type { SearchResult, MovieRec } from '../api/movies';
import PageTransition from '../components/layout/PageTransition';
import MovieGrid from '../components/movie/MovieGrid';
import useDebounce from '../hooks/useDebounce';
import './SearchPage.css';

export default function SearchPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialQuery = searchParams.get('q') || '';
  const [query, setQuery] = useState(initialQuery);
  const debouncedQuery = useDebounce(query, 300);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    document.title = query
      ? `Search: ${query} — CINEMATIC`
      : 'Search — CINEMATIC';
  }, [query]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  useEffect(() => {
    if (debouncedQuery) {
      setSearchParams({ q: debouncedQuery }, { replace: true });
    } else {
      setSearchParams({}, { replace: true });
    }
  }, [debouncedQuery, setSearchParams]);

  const { data, isLoading } = useQuery({
    queryKey: ['search', debouncedQuery],
    queryFn: () => searchMovies(debouncedQuery, 30),
    enabled: debouncedQuery.length >= 2,
    staleTime: 60_000,
  });

  // Convert SearchResult to MovieRec shape for MovieGrid
  const movies: MovieRec[] = (data?.results ?? []).map((r: SearchResult) => ({
    movieId: null,
    tmdbId: r.tmdbId,
    title: r.title,
    poster: null,
    scores: { content: null, collaborative: null, popularity: null, hybrid: null },
    metadata: null,
    source: 'search',
  }));

  const recentSearches = getRecentSearches();

  const handleQueryChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value);
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      saveRecentSearch(query.trim());
    }
  };

  const handleRecentClick = (term: string) => {
    setQuery(term);
    saveRecentSearch(term);
  };

  return (
    <PageTransition>
      <div className="search-page">
        <div className="search-page__header">
          <motion.form
            className="search-page__input-container"
            onSubmit={handleSubmit}
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
          >
            <Search className="search-page__icon" size={22} />
            <input
              ref={inputRef}
              type="text"
              className="search-page__input"
              placeholder="Search for movies..."
              value={query}
              onChange={handleQueryChange}
              autoComplete="off"
              spellCheck={false}
            />
            {query && (
              <button
                type="button"
                className="search-page__clear"
                onClick={() => setQuery('')}
              >
                Clear
              </button>
            )}
          </motion.form>
        </div>

        <div className="search-page__content">
          <AnimatePresence mode="wait">
            {debouncedQuery.length < 2 ? (
              <motion.div
                key="empty"
                className="search-page__empty"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              >
                <Film size={48} className="search-page__empty-icon" />
                <p className="search-page__empty-text">
                  Search across 23,000+ movies
                </p>
                {recentSearches.length > 0 && (
                  <div className="search-page__recent">
                    <p className="search-page__recent-label">Recent searches</p>
                    <div className="search-page__recent-tags">
                      {recentSearches.map((term) => (
                        <button
                          key={term}
                          className="search-page__recent-tag"
                          onClick={() => handleRecentClick(term)}
                        >
                          {term}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </motion.div>
            ) : (
              <motion.div
                key="results"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
              >
                {!isLoading && movies.length > 0 && (
                  <p className="search-page__count">
                    {data?.count ?? movies.length} results for "{debouncedQuery}"
                  </p>
                )}
                <MovieGrid
                  movies={movies}
                  loading={isLoading}
                  emptyMessage={`No movies found for "${debouncedQuery}"`}
                />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </PageTransition>
  );
}

// ── localStorage helpers ──────────────────────────────────

const RECENT_KEY = 'cinematic-recent-searches';
const MAX_RECENT = 8;

function getRecentSearches(): string[] {
  try {
    return JSON.parse(localStorage.getItem(RECENT_KEY) || '[]');
  } catch {
    return [];
  }
}

function saveRecentSearch(term: string) {
  const existing = getRecentSearches().filter((t) => t !== term);
  const updated = [term, ...existing].slice(0, MAX_RECENT);
  localStorage.setItem(RECENT_KEY, JSON.stringify(updated));
}
