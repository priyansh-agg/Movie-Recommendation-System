import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Home, ArrowLeft } from 'lucide-react';
import Button from '../components/ui/Button';
import PageTransition from '../components/layout/PageTransition';
import './NotFoundPage.css';

export default function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <PageTransition>
      <div className="not-found">
        <motion.div
          className="not-found__content"
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
        >
          <h1 className="not-found__code">404</h1>
          <h2 className="not-found__title">Page Not Found</h2>
          <p className="not-found__text">
            The page you're looking for doesn't exist or has been moved.
          </p>
          <div className="not-found__actions">
            <Button
              variant="primary"
              icon={<Home size={16} />}
              onClick={() => navigate('/')}
            >
              Go Home
            </Button>
            <Button
              variant="secondary"
              icon={<ArrowLeft size={16} />}
              onClick={() => {
                if (window.history.length > 1) navigate(-1);
                else navigate('/');
              }}
            >
              Go Back
            </Button>
          </div>
        </motion.div>
      </div>
    </PageTransition>
  );
}
