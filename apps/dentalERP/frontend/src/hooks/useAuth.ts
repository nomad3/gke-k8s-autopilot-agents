import { useAuthStore } from '../store/authStore';

export const useAuth = () => {
  const user = useAuthStore(state => state.user);
  const loading = useAuthStore(state => state.loading);
  const isAuthenticated = useAuthStore(state => state.isAuthenticated);

  return {
    user,
    loading,
    isAuthenticated,
  };
};
