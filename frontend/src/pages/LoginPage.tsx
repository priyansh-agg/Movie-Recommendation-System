import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Mail, Lock, ArrowRight } from 'lucide-react';
import PageTransition from '../components/layout/PageTransition';
import Input from '../components/ui/Input';
import Button from '../components/ui/Button';
import GlassCard from '../components/ui/GlassCard';
import { useAuthStore } from '../stores/authStore';
import { useToast } from '../components/ui/Toast';
import './AuthPages.css';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const login = useAuthStore((s) => s.login);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const { showToast } = useToast();

  useEffect(() => {
    document.title = 'Login — CINEMATIC';
    if (isAuthenticated) navigate('/', { replace: true });
  }, [isAuthenticated, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await login(email, password);
      showToast('Welcome back!', 'success');
      navigate('/');
    } catch (err: any) {
      const msg = err?.response?.data?.detail || 'Invalid email or password';
      setError(msg);
      showToast(msg, 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <PageTransition>
      <div className="auth-page">
        <div className="auth-page__ambient" />
        <motion.div
          className="auth-page__container"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
        >
          <GlassCard className="auth-card">
            <div className="auth-card__header">
              <h1 className="auth-card__title">Welcome Back</h1>
              <p className="auth-card__subtitle">
                Sign in to access your personalized recommendations
              </p>
            </div>

            <form onSubmit={handleSubmit} className="auth-card__form">
              <Input
                label="Email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                icon={<Mail size={18} />}
                error={undefined}
                autoComplete="email"
              />

              <Input
                label="Password"
                type="password"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                icon={<Lock size={18} />}
                error={error || undefined}
                autoComplete="current-password"
              />

              <Button
                type="submit"
                loading={loading}
                fullWidth
                icon={<ArrowRight size={18} />}
              >
                Sign In
              </Button>
            </form>

            <div className="auth-card__footer">
              <span className="auth-card__footer-text">
                Don't have an account?
              </span>
              <Link to="/register" className="auth-card__footer-link">
                Create one
              </Link>
            </div>
          </GlassCard>
        </motion.div>
      </div>
    </PageTransition>
  );
}
