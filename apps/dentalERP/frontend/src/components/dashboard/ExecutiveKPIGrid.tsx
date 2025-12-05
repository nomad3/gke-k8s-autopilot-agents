import { useQuery } from '@tanstack/react-query';
import React, { useEffect, useMemo } from 'react';
import { analyticsAPI } from '../../services/api';
import { useAuthStore } from '../../store/authStore';
import { useDashboardStore } from '../../store/dashboardStore';
import KPIWidget from '../widgets/KPIWidget';
import DashboardGrid from './DashboardGrid';

type Props = { practiceIds: string[] };

const ExecutiveKPIGrid: React.FC<Props> = ({ practiceIds }) => {
  const user = useAuthStore(s => s.user);
  const currentPractice = useAuthStore(s => s.currentPractice);
  const { layout, widgets, loadLayout, saveLayout } = useDashboardStore();

  const effectivePracticeId = currentPractice?.id || user?.practiceIds?.[0];

  useEffect(() => {
    if (effectivePracticeId) {
      loadLayout(effectivePracticeId);
    }
  }, [effectivePracticeId]);

  const { data: kpiRes, refetch } = useQuery({
    queryKey: ['executive-kpis', practiceIds.sort().join(',')],
    queryFn: async () => analyticsAPI.getExecutiveKPIs(practiceIds, '30d'),
    staleTime: 30_000,
  });

  useEffect(() => {
    const handler = () => { refetch(); };
    window.addEventListener('analytics-update', handler as any);
    return () => window.removeEventListener('analytics-update', handler as any);
  }, [refetch]);

  const items = useMemo(() => {
    const order = layout?.length ? layout.map(l => l.id) : [
      'kpi_total_revenue', 'kpi_patient_volume', 'kpi_appointment_efficiency', 'kpi_profit_margin'
    ];

    const map: Record<string, React.ReactNode> = {
      kpi_total_revenue: (
        <KPIWidget
          title="Total Revenue"
          value={
            kpiRes?.data?.totalRevenue?.value != null
              ? `$${(kpiRes.data.totalRevenue.value / 1_000_000).toFixed(1)}M`
              : '—'
          }
          change={
            kpiRes?.data?.totalRevenue?.change != null
              ? `${kpiRes.data.totalRevenue.change > 0 ? '+' : ''}${kpiRes.data.totalRevenue.change}%`
              : '—'
          }
          trend={kpiRes?.data?.totalRevenue?.trend || 'neutral'}
          source={kpiRes?.data?.totalRevenue?.source || 'Eaglesoft + DentalIntel'}
          icon={
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
          iconColor="green"
        />
      ),
      kpi_patient_volume: (
        <KPIWidget
          title="Patient Volume"
          value={
            kpiRes?.data?.patientVolume?.value != null
              ? kpiRes.data.patientVolume.value.toLocaleString()
              : '—'
          }
          change={
            kpiRes?.data?.patientVolume?.change != null
              ? `${kpiRes.data.patientVolume.change > 0 ? '+' : ''}${kpiRes.data.patientVolume.change}%`
              : '—'
          }
          trend={kpiRes?.data?.patientVolume?.trend || 'neutral'}
          source={kpiRes?.data?.patientVolume?.source || 'Dentrix + DentalIntel'}
          icon={
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          }
          iconColor="blue"
        />
      ),
      kpi_appointment_efficiency: (
        <KPIWidget
          title="Appointment Efficiency"
          value={
            kpiRes?.data?.appointmentEfficiency?.value != null
              ? `${kpiRes.data.appointmentEfficiency.value}%`
              : '—'
          }
          change={
            kpiRes?.data?.appointmentEfficiency?.change != null
              ? `${kpiRes.data.appointmentEfficiency.change > 0 ? '+' : ''}${kpiRes.data.appointmentEfficiency.change}%`
              : '—'
          }
          trend={kpiRes?.data?.appointmentEfficiency?.trend || 'neutral'}
          source={kpiRes?.data?.appointmentEfficiency?.source || 'Dentrix + Scheduling'}
          icon={
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          }
          iconColor="purple"
        />
      ),
      kpi_profit_margin: (
        <KPIWidget
          title="Profit Margin"
          value={
            kpiRes?.data?.profitMargin?.value != null
              ? `${kpiRes.data.profitMargin.value}%`
              : '—'
          }
          change={
            kpiRes?.data?.profitMargin?.change != null
              ? `${kpiRes.data.profitMargin.change > 0 ? '+' : ''}${kpiRes.data.profitMargin.change}%`
              : '—'
          }
          trend={kpiRes?.data?.profitMargin?.trend || 'neutral'}
          source={kpiRes?.data?.profitMargin?.source || 'Eaglesoft + ADP'}
          icon={
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          }
          iconColor="orange"
        />
      ),
    };

    return order
      .filter(id => id in map)
      .map(id => ({ id, content: map[id] }));
  }, [layout, kpiRes]);

  const handleReorder = async (newOrder: string[]) => {
    const nextLayout = newOrder.map(id => ({ id }));
    if (effectivePracticeId) {
      await saveLayout(effectivePracticeId, nextLayout, widgets || {});
    }
  };

  return (
    <DashboardGrid items={items} onReorder={handleReorder} />
  );
};

export default ExecutiveKPIGrid;
