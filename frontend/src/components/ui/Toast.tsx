import {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  useRef,
  type ReactNode,
} from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, CheckCircle, AlertCircle, Info } from 'lucide-react';
import './Toast.css';

type ToastType = 'success' | 'error' | 'info';

interface ToastItem {
  id: number;
  message: string;
  type: ToastType;
}

interface ToastContextValue {
  showToast: (message: string, type?: ToastType) => void;
}

const ToastContext = createContext<ToastContextValue>({
  showToast: () => {},
});

export function useToast() {
  return useContext(ToastContext);
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const nextIdRef = useRef(0);
  const timersRef = useRef<Map<number, ReturnType<typeof setTimeout>>>(new Map());

  // Clear all timers on unmount
  useEffect(() => {
    return () => {
      timersRef.current.forEach((timer) => clearTimeout(timer));
    };
  }, []);

  const dismiss = useCallback((id: number) => {
    const timer = timersRef.current.get(id);
    if (timer) { clearTimeout(timer); timersRef.current.delete(id); }
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const showToast = useCallback((message: string, type: ToastType = 'info') => {
    const id = ++nextIdRef.current;
    setToasts((prev) => {
      // Cap at 5 — drop oldest if at limit
      const capped = prev.length >= 5 ? prev.slice(1) : prev;
      return [...capped, { id, message, type }];
    });
    const timer = setTimeout(() => dismiss(id), 4000);
    timersRef.current.set(id, timer);
  }, [dismiss]);

  const icons: Record<ToastType, ReactNode> = {
    success: <CheckCircle size={18} />,
    error: <AlertCircle size={18} />,
    info: <Info size={18} />,
  };

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      <div className="toast-container">
        <AnimatePresence>
          {toasts.map((toast) => (
            <motion.div
              key={toast.id}
              className={`toast toast--${toast.type}`}
              initial={{ x: 120, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: 120, opacity: 0 }}
              transition={{ type: 'spring', stiffness: 400, damping: 30 }}
            >
              <span className="toast__icon">{icons[toast.type]}</span>
              <span className="toast__message">{toast.message}</span>
              <button
                className="toast__close"
                onClick={() => dismiss(toast.id)}
                aria-label="Dismiss notification"
              >
                <X size={14} />
              </button>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
}
