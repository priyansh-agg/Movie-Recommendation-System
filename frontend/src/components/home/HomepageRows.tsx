import type { HomepageSection } from '../../api/movies';
import MovieRow from '../movie/MovieRow';

interface HomepageRowsProps {
  sections: HomepageSection[];
  loading?: boolean;
}

export default function HomepageRows({ sections, loading }: HomepageRowsProps) {
  if (loading) {
    return (
      <>
        {['Trending Now', 'Top Rated', 'Popular', 'New Releases'].map((title) => (
          <MovieRow key={title} title={title} movies={[]} loading />
        ))}
      </>
    );
  }

  return (
    <>
      {sections
        .filter((s) => s.movies.length > 0)
        .map((section) => (
          <MovieRow
            key={section.title}
            title={section.title}
            movies={section.movies}
          />
        ))}
    </>
  );
}
