export type DateRange = '7d' | '30d' | '90d' | '6m' | '12m' | 'ytd' | string;

// Prefer relative default so Vite dev proxy or Nginx can route to backend
const base = (import.meta.env.VITE_API_BASE_URL as string | undefined) || '/api';
const API_BASE = `${base.replace(/\/$/, '')}/analytics`;

function authHeader(): Record<string, string> {
  const token = localStorage.getItem('access_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function getExecutiveKPIs(practiceIds: string[] = [], dateRange?: DateRange) {
  const params = new URLSearchParams();
  if (practiceIds.length) params.set('practiceIds', practiceIds.join(','));
  if (dateRange) params.set('dateRange', dateRange);
  const res = await fetch(`${API_BASE}/executive-kpis?${params}`, { headers: { 'Content-Type': 'application/json', ...authHeader() } });
  if (!res.ok) throw new Error('Failed to fetch executive KPIs');
  return res.json();
}

export async function getRevenueTrends(practiceIds: string[] = [], dateRange?: DateRange) {
  const params = new URLSearchParams();
  if (practiceIds.length) params.set('practiceIds', practiceIds.join(','));
  if (dateRange) params.set('dateRange', dateRange);
  const res = await fetch(`${API_BASE}/revenue-trends?${params}`, { headers: { 'Content-Type': 'application/json', ...authHeader() } });
  if (!res.ok) throw new Error('Failed to fetch revenue trends');
  return res.json();
}

export async function getLocationPerformance(practiceIds: string[] = [], dateRange?: DateRange) {
  const params = new URLSearchParams();
  if (practiceIds.length) params.set('practiceIds', practiceIds.join(','));
  if (dateRange) params.set('dateRange', dateRange);
  const res = await fetch(`${API_BASE}/location-performance?${params}`, { headers: { 'Content-Type': 'application/json', ...authHeader() } });
  if (!res.ok) throw new Error('Failed to fetch location performance');
  return res.json();
}

export async function getManagerMetrics(practiceId: string, date?: string) {
  const params = new URLSearchParams();
  params.set('practiceId', practiceId);
  if (date) params.set('date', date);
  const res = await fetch(`${API_BASE}/manager-metrics?${params}`, { headers: { 'Content-Type': 'application/json', ...authHeader() } });
  if (!res.ok) throw new Error('Failed to fetch manager metrics');
  return res.json();
}

export async function getClinicalMetrics(providerId: string, dateRange?: DateRange) {
  const params = new URLSearchParams();
  params.set('providerId', providerId);
  if (dateRange) params.set('dateRange', dateRange);
  const res = await fetch(`${API_BASE}/clinical-metrics?${params}`, { headers: { 'Content-Type': 'application/json', ...authHeader() } });
  if (!res.ok) throw new Error('Failed to fetch clinical metrics');
  return res.json();
}

export async function getIntegrationStatus() {
  const res = await fetch(`${API_BASE}/integration-status`, { headers: { 'Content-Type': 'application/json', ...authHeader() } });
  if (!res.ok) throw new Error('Failed to fetch integration status');
  return res.json();
}
