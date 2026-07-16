import { useState } from 'react';
import { motion } from 'framer-motion';
import { Star } from 'lucide-react';
import './RatingStars.css';

interface RatingStarsProps {
  value: number;
  onChange?: (rating: number) => void;
  size?: 'sm' | 'md' | 'lg';
  readonly?: boolean;
}

const sizes = { sm: 16, md: 20, lg: 24 };

export default function RatingStars({
  value,
  onChange,
  size = 'md',
  readonly = false,
}: RatingStarsProps) {
  const [hoverValue, setHoverValue] = useState(0);
  const iconSize = sizes[size];
  const displayValue = hoverValue || value;

  return (
    <div className={`rating-stars rating-stars--${size}`}>
      <div
        className="rating-stars__stars"
        onMouseLeave={() => !readonly && setHoverValue(0)}
      >
        {[1, 2, 3, 4, 5].map((star) => {
          const filled = displayValue >= star;
          const halfFilled = displayValue >= star - 0.5 && displayValue < star;

          return (
            <motion.button
              key={star}
              type="button"
              className={`rating-stars__star ${filled || halfFilled ? 'rating-stars__star--active' : ''}`}
              disabled={readonly}
              onMouseEnter={() => !readonly && setHoverValue(star)}
              onClick={() => onChange?.(star)}
              whileTap={readonly ? {} : { scale: 1.25 }}
              transition={{ type: 'spring', stiffness: 400, damping: 15 }}
            >
              <Star
                size={iconSize}
                fill={filled || halfFilled ? 'var(--rating-gold)' : 'transparent'}
                stroke={filled || halfFilled ? 'var(--rating-gold)' : 'var(--text-muted)'}
              />
            </motion.button>
          );
        })}
      </div>
      {value > 0 && (
        <span className="rating-stars__value">{value.toFixed(1)}</span>
      )}
    </div>
  );
}
