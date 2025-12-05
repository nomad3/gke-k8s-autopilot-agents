import React, { useEffect, useState } from 'react';
import { useAuthStore } from '../store/authStore';
import { authAPI } from '../services/api';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';

interface AuthProviderProps {
  children: React.ReactNode;
}

// Ensures auth state is hydrated before rendering protected routes
export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const setLoading = useAuthStore((s) => s.setLoading);
  const setInitialized = useAuthStore((s) => s.setInitialized);
  const setUser = useAuthStore((s) => s.setUser);
  const clearAuth = useAuthStore((s) => s.clearAuth);
  const loading = useAuthStore((s) => s.loading);

  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const rehydrate = async () => {
      try {
        setLoading(true);

        // Wait for zustand-persist to finish (best-effort across versions)
        // Prefer built-in helpers when available
        const anyStore: any = useAuthStore as any;
        if (anyStore.persist?.hasHydrated) {
          if (!anyStore.persist.hasHydrated()) {
            await anyStore.persist.rehydrate?.();
          }
        }

        if (cancelled) return;

        // Get fresh token state after hydration
        const state = useAuthStore.getState();
        const hasTokens = !!(state.accessToken || state.refreshToken);

        setHydrated(true);
        setInitialized(true);

        // If we already have tokens, verify session and fetch profile
        if (hasTokens) {
          try {
            const profile = await authAPI.getProfile();
            if (!cancelled) {
              setUser(profile?.data || profile?.user || profile || null);
            }
          } catch (e: any) {
            // Only clear auth if it's an actual authentication error (401/403)
            // The axios interceptor will have already tried to refresh the token
            // Network errors or other issues should not log the user out
            const isAuthError = e?.response?.status === 401 || e?.response?.status === 403;
            if (!cancelled && isAuthError) {
              console.warn('Session expired or invalid, clearing auth');
              clearAuth();
            } else if (!cancelled && e?.code !== 'ERR_NETWORK') {
              // For non-network errors that aren't auth errors, log but don't clear
              console.warn('Failed to fetch profile, but keeping session:', e?.message);
            }
          }
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    rehydrate();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // While hydrating/loading, render a minimal loader to avoid premature redirects
  if (!hydrated || loading) {
    return (
      <div className="min-h-screen w-full flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return <>{children}</>;
};
