import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Mail, Lock, User, ArrowRight } from 'lucide-react';
import PageTransition from '../components/layout/PageTransition';
import Input from '../components/ui/Input';
import Button from '../components/ui/Button';
import GlassCard from '../components/ui/GlassCard';
import { useAuthStore } from '../stores/authStore';
import { useToast } from '../components/ui/Toast';
import './AuthPages.css';

export default function RegisterPage() {
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const register = useAuthStore((s) => s.register);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const { showToast } = useToast();

  useEffect(() => {
    document.title = 'Sign Up — CINEMATIC';
    if (isAuthenticated) navigate('/', { replace: true });
  }, [isAuthenticated, navigate]);

  const validate = (): boolean => {
    const errs: Record<string, string> = {};
    if (!email.includes('@')) errs.email = 'Enter a valid email address';
    if (username.length < 2) errs.username = 'Username must be at least 2 characters';
    if (password.length < 6) errs.password = 'Password must be at least 6 characters';
    if (password !== confirmPassword) errs.confirm = 'Passwords do not match';
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    setLoading(true);
    try {
      await register(email, username, password);
      showToast('Account created successfully!', 'success');
      navigate('/onboarding');
    } catch (err: any) {
      const msg = err?.response?.data?.detail || 'Registration failed';
      setErrors({ form: msg });
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
              <h1 className="auth-card__title">Create Account</h1>
              <p className="auth-card__subtitle">
                Join to get personalized movie recommendations
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
                error={errors.email}
                autoComplete="email"
              />

              <Input
                label="Username"
                type="text"
                placeholder="Choose a username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                icon={<User size={18} />}
                error={errors.username}
                autoComplete="username"
              />

              <Input
                label="Password"
                type="password"
                placeholder="At least 6 characters"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                icon={<Lock size={18} />}
                error={errors.password}
                autoComplete="new-password"
              />

              <Input
                label="Confirm Password"
                type="password"
                placeholder="Re-enter your password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                icon={<Lock size={18} />}
                error={errors.confirm}
                autoComplete="new-password"
              />

              {errors.form && (
                <p className="auth-card__error">{errors.form}</p>
              )}

              <Button
                type="submit"
                loading={loading}
                fullWidth
                icon={<ArrowRight size={18} />}
              >
                Create Account
              </Button>
            </form>

            <div className="auth-card__footer">
              <span className="auth-card__footer-text">
                Already have an account?
              </span>
              <Link to="/login" className="auth-card__footer-link">
                Sign in
              </Link>
            </div>
          </GlassCard>
        </motion.div>
      </div>
    </PageTransition>
  );
}
