import { create } from 'zustand';
import { createJSONStorage, persist } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';

export interface User {
  id: string;
  email: string;
  firstName: string;
  lastName: string;
  role: 'admin' | 'executive' | 'manager' | 'clinician' | 'staff';
  avatar?: string;
  phone?: string;
  preferences?: Record<string, any>;
  practiceIds: string[];
  currentPracticeId?: string;
}

export interface Practice {
  id: string;
  name: string;
  address: {
    street: string;
    city: string;
    state: string;
    zipCode: string;
    country: string;
  };
  phone?: string;
  email?: string;
  website?: string;
}

interface AuthState {
  // State
  user: User | null;
  practices: Practice[];
  currentPractice: Practice | null;
  accessToken: string | null;
  refreshToken: string | null;
  loading: boolean;
  initialized: boolean;

  // Actions
  setUser: (user: User | null) => void;
  setTokens: (accessToken: string, refreshToken: string) => void;
  setPractices: (practices: Practice[]) => void;
  setCurrentPractice: (practiceId: string) => void;
  setLoading: (loading: boolean) => void;
  setInitialized: (initialized: boolean) => void;
  updateUserPreferences: (preferences: Record<string, any>) => void;
  clearAuth: () => void;

  // Computed getters
  isAuthenticated: boolean;
  canAccessPractice: (practiceId: string) => boolean;
  hasRole: (roles: string | string[]) => boolean;
  hasPermission: (permission: string) => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    immer((set, get) => ({
      // Initial state
      user: null,
      practices: [],
      currentPractice: null,
      accessToken: null,
      refreshToken: null,
      loading: false,
      initialized: false,

      // Actions
      setUser: (user) =>
        set((state) => {
          state.user = user;
          // If user is null, also clear practices and current practice
          if (!user) {
            state.practices = [];
            state.currentPractice = null;
          }
        }),

      setTokens: (accessToken, refreshToken) =>
        set((state) => {
          state.accessToken = accessToken;
          state.refreshToken = refreshToken;
        }),

      setPractices: (practices) =>
        set((state) => {
          state.practices = practices;
          // Set current practice to first practice if not set
          if (practices.length > 0 && !state.currentPractice) {
            state.currentPractice = practices[0] ?? null;
          }
        }),

      setCurrentPractice: (practiceId) =>
        set((state) => {
          const practice = state.practices.find((p) => p.id === practiceId);
          if (practice && state.user?.practiceIds.includes(practiceId)) {
            state.currentPractice = practice;
            // Update user's current practice ID
            if (state.user) {
              state.user.currentPracticeId = practiceId;
            }
          }
        }),

      setLoading: (loading) =>
        set((state) => {
          state.loading = loading;
        }),

      setInitialized: (initialized) =>
        set((state) => {
          state.initialized = initialized;
        }),

      updateUserPreferences: (preferences) =>
        set((state) => {
          if (state.user) {
            state.user.preferences = {
              ...state.user.preferences,
              ...preferences,
            };
          }
        }),

      clearAuth: () =>
        set((state) => {
          state.user = null;
          state.practices = [];
          state.currentPractice = null;
          state.accessToken = null;
          state.refreshToken = null;
          state.loading = false;
        }),

      // Computed getters
      get isAuthenticated() {
        const state = get();
        return !!(state.user && state.accessToken);
      },

      canAccessPractice: (practiceId: string) => {
        const state = get();
        if (!state.user) return false;

        // Admin and executive roles can access all practices
        if (['admin', 'executive'].includes(state.user.role)) {
          return true;
        }

        return state.user.practiceIds.includes(practiceId);
      },

      hasRole: (roles: string | string[]) => {
        const state = get();
        if (!state.user) return false;

        const allowedRoles = Array.isArray(roles) ? roles : [roles];
        return allowedRoles.includes(state.user.role);
      },

      hasPermission: (permission: string) => {
        const state = get();
        if (!state.user) return false;

        // Admin has all permissions
        if (state.user.role === 'admin') return true;

        // Check role-based permissions
        const rolePermissions = getRolePermissions(state.user.role);
        return rolePermissions.includes(permission);
      },
    })),
    {
      name: 'dental-erp-auth',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        user: state.user,
        practices: state.practices,
        currentPractice: state.currentPractice,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
      }),
    }
  )
);

// Helper function to get role-based permissions
function getRolePermissions(role: string): string[] {
  const permissions: Record<string, string[]> = {
    admin: ['*'], // All permissions
    executive: [
      'dashboard:read',
      'analytics:read',
      'reports:read',
      'practices:read',
      'staff:read',
      'integrations:read',
    ],
    manager: [
      'dashboard:read',
      'patients:read',
      'patients:write',
      'appointments:read',
      'appointments:write',
      'staff:read',
      'schedule:write',
      'reports:read',
    ],
    clinician: [
      'dashboard:read',
      'patients:read',
      'patients:write',
      'appointments:read',
      'treatments:read',
      'treatments:write',
      'notes:read',
      'notes:write',
    ],
    staff: [
      'dashboard:read',
      'appointments:read',
      'patients:read',
      'checkin:write',
    ],
  };

  return permissions[role] || [];
}

// Selectors for better performance
export const selectUser = (state: AuthState) => state.user;
export const selectIsAuthenticated = (state: AuthState) => state.isAuthenticated;
export const selectCurrentPractice = (state: AuthState) => state.currentPractice;
export const selectPractices = (state: AuthState) => state.practices;
export const selectLoading = (state: AuthState) => state.loading;
export const selectTokens = (state: AuthState) => ({
  accessToken: state.accessToken,
  refreshToken: state.refreshToken,
});

// Custom hooks for common use cases
export const useAuthUser = () => useAuthStore(selectUser);
export const useIsAuthenticated = () => useAuthStore(selectIsAuthenticated);
export const useCurrentPractice = () => useAuthStore(selectCurrentPractice);
export const usePractices = () => useAuthStore(selectPractices);
export const useAuthLoading = () => useAuthStore(selectLoading);

export default useAuthStore;
