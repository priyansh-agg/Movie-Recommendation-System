import { useEffect } from 'react';
import { User, Star, Heart, Bookmark, Film, LogOut } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useAuthStore } from '../stores/authStore';
import PageTransition from '../components/layout/PageTransition';
import GlassCard from '../components/ui/GlassCard';
import Button from '../components/ui/Button';
import './ProfilePage.css';

export default function ProfilePage() {
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const fetchProfile = useAuthStore((s) => s.fetchProfile);
  const navigate = useNavigate();

  useEffect(() => {
    document.title = 'Profile — CINEMATIC';
    fetchProfile();
  }, [fetchProfile]);

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  const stats = [
    { icon: <Star size={20} />, label: 'Ratings', value: user?.ratings_count ?? 0 },
    { icon: <Heart size={20} />, label: 'Liked', value: user?.liked_count ?? 0 },
    { icon: <Bookmark size={20} />, label: 'Watchlist', value: user?.watchlist?.length ?? 0 },
    { icon: <Film size={20} />, label: 'Watched', value: user?.watch_history?.length ?? 0 },
  ];

  return (
    <PageTransition>
      <div className="profile-page">
        <div className="profile-page__header">
          <div className="profile-page__avatar">
            {(user?.username?.[0] || 'U').toUpperCase()}
          </div>
          <div className="profile-page__user-info">
            <h1>{user?.username || 'User'}</h1>
            <p>{user?.email}</p>
          </div>
        </div>

        <div className="profile-page__stats">
          {stats.map((stat, i) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
            >
              <GlassCard className="profile-page__stat-card" padding="20px">
                <span className="profile-page__stat-icon">{stat.icon}</span>
                <span className="profile-page__stat-value">{stat.value}</span>
                <span className="profile-page__stat-label">{stat.label}</span>
              </GlassCard>
            </motion.div>
          ))}
        </div>

        {user?.preferences && user.preferences.favorite_genres.length > 0 && (
          <GlassCard className="profile-page__prefs" padding="24px">
            <h2>Favorite Genres</h2>
            <div className="profile-page__genres">
              {user.preferences.favorite_genres.map((g) => (
                <span key={g} className="profile-page__genre-pill">{g}</span>
              ))}
            </div>
          </GlassCard>
        )}

        <div className="profile-page__actions">
          <Button variant="ghost" icon={<LogOut size={16} />} onClick={handleLogout}>
            Sign Out
          </Button>
        </div>
      </div>
    </PageTransition>
  );
}
