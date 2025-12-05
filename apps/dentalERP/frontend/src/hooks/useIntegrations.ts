import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { integrationCredentialsAPI } from '../services/api';
import { useAuthStore } from '../store/authStore';

const QUERY_KEY = ['integration-credentials'];

export const useIntegrationCredentialSummaries = (practiceId?: string) => {
  const user = useAuthStore((state) => state.user);

  return useQuery({
    queryKey: [...QUERY_KEY, practiceId ?? 'all'],
    queryFn: () => integrationCredentialsAPI.listSummaries(practiceId ? { practiceId } : undefined),
    enabled: Boolean(user),
  });
};

export const useIntegrationCredentialMutations = () => {
  const queryClient = useQueryClient();

  const invalidate = () => {
    void queryClient.invalidateQueries({ queryKey: QUERY_KEY });
  };

  const upsert = useMutation({
    mutationFn: (
      params: {
        practiceId: string;
        integrationType: string;
        name: string;
        credentials: Record<string, string>;
        metadata?: Record<string, unknown>;
      },
    ) => integrationCredentialsAPI.upsertCredential(params.practiceId, params.integrationType, {
      name: params.name,
      credentials: params.credentials,
      metadata: params.metadata,
    }),
    onSuccess: invalidate,
  });

  const remove = useMutation({
    mutationFn: (params: { practiceId: string; integrationType: string }) =>
      integrationCredentialsAPI.deleteCredential(params.practiceId, params.integrationType),
    onSuccess: invalidate,
  });

  return { upsert, remove };
};
