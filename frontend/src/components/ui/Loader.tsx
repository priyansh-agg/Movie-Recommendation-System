import './Loader.css';

interface LoaderProps {
  size?: 'sm' | 'md' | 'lg';
  fullPage?: boolean;
}

export default function Loader({ size = 'md', fullPage = false }: LoaderProps) {
  const spinner = <span className={`loader loader--${size}`} />;

  if (fullPage) {
    return <div className="loader-fullpage">{spinner}</div>;
  }
  return spinner;
}
