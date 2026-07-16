import { type ReactNode } from 'react';
import './GlassCard.css';

interface GlassCardProps {
  children: ReactNode;
  className?: string;
  hover?: boolean;
  padding?: string;
  onClick?: () => void;
}

export default function GlassCard({
  children,
  className = '',
  hover = false,
  padding = '24px',
  onClick,
}: GlassCardProps) {
  return (
    <div
      className={`glass-card ${hover ? 'glass-card--hover' : ''} ${className}`}
      style={{ padding }}
      onClick={onClick}
    >
      {children}
    </div>
  );
}
