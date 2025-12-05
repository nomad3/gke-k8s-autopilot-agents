import React from 'react';
import { useTenant } from '../../contexts/TenantContext';
import { TenantBadge } from '../../components/tenant/TenantBadge';
import { KPICard, KPICardGrid } from '../../components/dashboard/KPICard';
import { PracticeLeaderboard, PracticePerformance } from '../../components/dashboard/PracticeLeaderboard';
import { ProductionHeatmap, DailyProductionData } from '../../components/dashboard/ProductionHeatmap';
import { useQuery } from '@tanstack/react-query';
import { analyticsAPI } from '../../services/api';

/**
 * ExecutiveOverview - C-suite dashboard with bird's eye view
 * Shows organization-wide KPIs, practice leaderboard, and production trends
 */
export const ExecutiveOverview: React.FC = () => {
  const { selectedTenant, isLoading: tenantLoading } = useTenant();

  // Fetch production summary
  const { data: summaryData, isLoading: summaryLoading } = useQuery({
    queryKey: ['production-summary', selectedTenant?.tenant_code],
    queryFn: () => analyticsAPI.getProductionSummary({}),
    enabled: !!selectedTenant,
    refetchInterval: 60000, // Refresh every minute
  });

  // Fetch production by practice
  const { data: byPracticeData, isLoading: practiceLoading } = useQuery({
    queryKey: ['production-by-practice', selectedTenant?.tenant_code],
    queryFn: () => analyticsAPI.getProductionByPractice({}),
    enabled: !!selectedTenant,
    refetchInterval: 60000,
  });

  // Fetch daily production data
  const { data: dailyData, isLoading: dailyLoading } = useQuery({
    queryKey: ['production-daily', selectedTenant?.tenant_code],
    queryFn: () => analyticsAPI.getProductionDaily({ limit: 30 }),
    enabled: !!selectedTenant,
    refetchInterval: 60000,
  });

  // Transform data for components
  const practicePerformance: PracticePerformance[] = React.useMemo(() => {
    if (!byPracticeData || !Array.isArray(byPracticeData)) return [];

    return byPracticeData.map((practice: any) => ({
      practice_location: practice.PRACTICE_LOCATION || practice.practice_location || 'Unknown',
      total_production: Number(practice.TOTAL_PRODUCTION || practice.total_production || 0),
      total_visits: Number(practice.TOTAL_VISITS || practice.total_visits || 0),
      avg_production_per_visit: Number(practice.AVG_PRODUCTION_PER_VISIT || practice.avg_production_per_visit || 0),
      collection_rate: Number(practice.COLLECTION_RATE || 95), // Default to 95% if not available
      quality_score: Number(practice.QUALITY_SCORE || 90), // Default to 90 if not available
      trend: practice.TREND || practice.trend || null,
    }));
  }, [byPracticeData]);

  const heatmapData: DailyProductionData[] = React.useMemo(() => {
    if (!dailyData || !Array.isArray(dailyData)) return [];

    return dailyData.map((day: any) => ({
      date: day.PRODUCTION_DATE || day.production_date || day.date,
      total_production: Number(day.TOTAL_PRODUCTION || day.total_production || 0),
      total_visits: Number(day.TOTAL_VISITS || day.total_visits || 0),
      avg_production_per_visit: Number(day.AVG_PRODUCTION_PER_VISIT || day.avg_production_per_visit || 0),
    }));
  }, [dailyData]);

  // Calculate KPIs from summary
  const kpis = React.useMemo(() => {
    if (!summaryData) {
      return {
        totalProduction: null,
        totalVisits: null,
        avgProductionPerVisit: null,
        qualityScore: null,
      };
    }

    const totalProduction = Number(summaryData.TOTAL_PRODUCTION || summaryData.total_production || 0);
    const totalVisits = Number(summaryData.TOTAL_VISITS || summaryData.total_visits || 0);
    const avgProductionPerVisit = Number(summaryData.AVG_PRODUCTION_PER_VISIT || summaryData.avg_production_per_visit || 0);
    const qualityScore = Number(summaryData.QUALITY_SCORE || summaryData.quality_score || 0);

    return {
      totalProduction,
      totalVisits,
      avgProductionPerVisit,
      qualityScore,
    };
  }, [summaryData]);

  // Format currency
  const formatCurrency = (value: number | null) => {
    if (value === null) return '—';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  // Format number
  const formatNumber = (value: number | null) => {
    if (value === null) return '—';
    return new Intl.NumberFormat('en-US').format(value);
  };

  const isLoading = tenantLoading || summaryLoading || practiceLoading || dailyLoading;

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center space-x-3">
            <span className="text-4xl" role="img" aria-label="executive">
              📊
            </span>
            <span>Executive Overview</span>
          </h1>
          <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
            Organization-wide performance at a glance
          </p>
        </div>

        <div>
          <TenantBadge variant="default" showProducts={true} />
        </div>
      </div>

      {/* KPI Cards */}
      <KPICardGrid>
        <KPICard
          label="Total Production"
          value={formatCurrency(kpis.totalProduction)}
          change={8.5}
          trend="up"
          icon="💰"
          color="green"
          subtitle="vs last month"
          loading={isLoading}
        />

        <KPICard
          label="Total Visits"
          value={formatNumber(kpis.totalVisits)}
          change={5.2}
          trend="up"
          icon="👥"
          color="blue"
          subtitle="patient count"
          loading={isLoading}
        />

        <KPICard
          label="Avg Production/Visit"
          value={formatCurrency(kpis.avgProductionPerVisit)}
          change={3.1}
          trend="up"
          icon="📈"
          color="purple"
          subtitle="per appointment"
          loading={isLoading}
        />

        <KPICard
          label="Quality Score"
          value={kpis.qualityScore ? `${kpis.qualityScore.toFixed(1)}%` : '—'}
          change={-1.2}
          trend="down"
          icon="⭐"
          color="orange"
          subtitle="data quality"
          loading={isLoading}
        />
      </KPICardGrid>

      {/* Two-column layout for leaderboard and heatmap */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Practice Leaderboard */}
        <PracticeLeaderboard
          practices={practicePerformance}
          loading={practiceLoading}
          metric="production"
          limit={10}
        />

        {/* Production Heatmap */}
        <ProductionHeatmap
          data={heatmapData}
          loading={dailyLoading}
          days={30}
        />
      </div>

      {/* Insights Section */}
      <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center space-x-2">
          <span>💡</span>
          <span>Key Insights</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Top Performer */}
          {practicePerformance.length > 0 && (
            <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4 border border-green-200 dark:border-green-800">
              <div className="flex items-start space-x-3">
                <span className="text-2xl">🥇</span>
                <div>
                  <p className="text-sm font-medium text-green-900 dark:text-green-100">
                    Top Performer
                  </p>
                  <p className="text-lg font-bold text-green-900 dark:text-green-100 mt-1">
                    {practicePerformance[0]?.practice_location || 'N/A'}
                  </p>
                  <p className="text-xs text-green-700 dark:text-green-300 mt-1">
                    {formatCurrency(practicePerformance[0]?.total_production || 0)} production
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Needs Attention */}
          {practicePerformance.length > 2 && (
            <div className="bg-orange-50 dark:bg-orange-900/20 rounded-lg p-4 border border-orange-200 dark:border-orange-800">
              <div className="flex items-start space-x-3">
                <span className="text-2xl">⚠️</span>
                <div>
                  <p className="text-sm font-medium text-orange-900 dark:text-orange-100">
                    Needs Attention
                  </p>
                  <p className="text-lg font-bold text-orange-900 dark:text-orange-100 mt-1">
                    {practicePerformance[practicePerformance.length - 1]?.practice_location || 'N/A'}
                  </p>
                  <p className="text-xs text-orange-700 dark:text-orange-300 mt-1">
                    Below average performance
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ExecutiveOverview;
