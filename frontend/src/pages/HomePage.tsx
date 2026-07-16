import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getHomepage } from '../api/movies';
import type { HomepageSection, MovieRec } from '../api/movies';
import PageTransition from '../components/layout/PageTransition';
import HeroBanner from '../components/home/HeroBanner';
import HomepageRows from '../components/home/HomepageRows';
import Loader from '../components/ui/Loader';
import './HomePage.css';

export default function HomePage() {
  const { data, isLoading, error } = useQuery<{ sections: HomepageSection[] }>({
    queryKey: ['homepage'],
    queryFn: getHomepage,
    staleTime: 5 * 60 * 1000,
  });

  const sections = data?.sections ?? [];
  const heroMovie = findHeroMovie(sections);

  useEffect(() => {
    document.title = 'CINEMATIC — Discover Your Next Favorite Movie';
  }, []);

  if (isLoading) {
    return <Loader fullPage />;
  }

  if (error) {
    return (
      <PageTransition>
        <div className="home-error">
          <p>Failed to load recommendations. Please try again later.</p>
        </div>
      </PageTransition>
    );
  }

  return (
    <PageTransition>
      <div className="home">
        {heroMovie && <HeroBanner movie={heroMovie} />}
        <div className="home__content">
          <HomepageRows sections={sections} loading={isLoading} />
        </div>
      </div>
    </PageTransition>
  );
}

function findHeroMovie(sections: HomepageSection[]): MovieRec | null {
  for (const section of sections) {
    for (const movie of section.movies) {
      if (
        movie.metadata?.poster_path &&
        movie.metadata?.overview &&
        (movie.metadata?.vote_average ?? 0) >= 7
      ) {
        return movie;
      }
    }
  }
  // Fallback to first movie with a poster
  for (const section of sections) {
    if (section.movies.length > 0 && section.movies[0].metadata?.poster_path) {
      return section.movies[0];
    }
  }
  return sections[0]?.movies[0] ?? null;
}
