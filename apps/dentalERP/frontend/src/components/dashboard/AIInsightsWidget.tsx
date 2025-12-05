import { useQuery } from '@tanstack/react-query';
import { ArrowPathIcon, SparklesIcon } from '@heroicons/react/24/solid';
import api from '../../services/api';

interface AIInsightsResponse {
  insight: string;
  practice_name: string;
  period: string;
  generated_at: string;
  model: string;
}

export function AIInsightsWidget() {
  const { data, isLoading, error, refetch } = useQuery<AIInsightsResponse>({
    queryKey: ['ai-insights'],
    queryFn: async () => {
      // Now uses backend proxy instead of direct MCP call
      const response = await api.get('/analytics/insights');
      return response.data;
    },
    staleTime: 60 * 60 * 1000,  // 1 hour (matches backend cache)
    retry: 1
  });

  if (isLoading) {
    return (
      <div className="bg-gradient-to-br from-purple-50 to-blue-50 rounded-lg shadow border border-purple-200 p-6">
        <div className="flex items-center space-x-3 text-purple-600">
          <SparklesIcon className="w-6 h-6 animate-pulse" />
          <span className="font-medium">Generating AI insights...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-gradient-to-br from-purple-50 to-blue-50 rounded-lg shadow border border-purple-200 p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <SparklesIcon className="w-6 h-6 text-purple-600" />
            <h3 className="font-semibold text-lg text-gray-900">AI Insights</h3>
          </div>
          <button
            onClick={() => refetch()}
            className="text-sm text-purple-600 hover:text-purple-700 flex items-center space-x-1"
          >
            <ArrowPathIcon className="w-4 h-4" />
            <span>Retry</span>
          </button>
        </div>
        <p className="mt-4 text-orange-600 text-sm">
          AI insights temporarily unavailable. Please try again.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-gradient-to-br from-purple-50 to-blue-50 rounded-lg shadow border border-purple-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <SparklesIcon className="w-6 h-6 text-purple-600" />
          <h3 className="font-semibold text-lg text-gray-900">AI Insights</h3>
        </div>
        <button
          onClick={() => refetch()}
          className="text-sm text-purple-600 hover:text-purple-700 flex items-center space-x-1 transition-colors"
        >
          <ArrowPathIcon className="w-4 h-4" />
          <span>Refresh</span>
        </button>
      </div>

      <div className="mb-4">
        <p className="text-gray-800 text-base leading-relaxed">
          {data?.insight}
        </p>
      </div>

      <div className="flex justify-between items-center text-xs text-gray-500">
        <span>Powered by GPT-4</span>
        {data?.generated_at && (
          <span>
            Updated {new Date(data.generated_at).toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit'
            })}
          </span>
        )}
      </div>
    </div>
  );
}
