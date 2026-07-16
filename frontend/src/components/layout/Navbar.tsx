import { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Search, User, Bookmark, LogOut } from 'lucide-react';
import { motion } from 'framer-motion';
import { useAuthStore } from '../../stores/authStore';
import Button from '../ui/Button';
import './Navbar.css';

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  useEffect(() => {
    const onClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', onClickOutside);
    return () => document.removeEventListener('mousedown', onClickOutside);
  }, []);

  const handleLogout = () => {
    logout();
    setDropdownOpen(false);
    navigate('/');
  };

  return (
    <motion.nav
      className={`navbar ${scrolled ? 'navbar--scrolled' : ''}`}
      initial={{ y: -64 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
    >
      <div className="navbar__inner">
        {/* Left: Logo + Links */}
        <div className="navbar__left">
          <Link to="/" className="navbar__logo">CINEMATIC</Link>
          <div className="navbar__links">
            <Link to="/" className="navbar__link">Home</Link>
            {isAuthenticated && (
              <Link to="/watchlist" className="navbar__link">Watchlist</Link>
            )}
          </div>
        </div>

        {/* Center: Search */}
        <button
          className="navbar__search"
          onClick={() => navigate('/search')}
        >
          <Search size={16} />
          <span>Search movies...</span>
        </button>

        {/* Right: Auth */}
        <div className="navbar__right">
          {isAuthenticated ? (
            <div className="navbar__user" ref={dropdownRef}>
              <button
                className="navbar__avatar"
                onClick={() => setDropdownOpen(!dropdownOpen)}
              >
                {(user?.username?.[0] || 'U').toUpperCase()}
              </button>

              {dropdownOpen && (
                <motion.div
                  className="navbar__dropdown"
                  initial={{ opacity: 0, y: -8 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.15 }}
                >
                  <Link
                    to="/profile"
                    className="navbar__dropdown-item"
                    onClick={() => setDropdownOpen(false)}
                  >
                    <User size={16} /> Profile
                  </Link>
                  <Link
                    to="/watchlist"
                    className="navbar__dropdown-item"
                    onClick={() => setDropdownOpen(false)}
                  >
                    <Bookmark size={16} /> Watchlist
                  </Link>
                  <button
                    className="navbar__dropdown-item navbar__dropdown-item--danger"
                    onClick={handleLogout}
                  >
                    <LogOut size={16} /> Logout
                  </button>
                </motion.div>
              )}
            </div>
          ) : (
            <div className="navbar__auth-buttons">
              <Button variant="ghost" size="sm" onClick={() => navigate('/login')}>
                Login
              </Button>
              <Button variant="primary" size="sm" onClick={() => navigate('/register')}>
                Sign Up
              </Button>
            </div>
          )}
        </div>
      </div>
    </motion.nav>
  );
}
