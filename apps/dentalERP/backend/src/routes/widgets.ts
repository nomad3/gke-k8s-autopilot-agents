import { Router } from 'express';

const router = Router();

// Static catalog of available widgets for MVP
router.get('/', (_req, res) => {
  const widgets = [
    { id: 'kpi_total_revenue', name: 'Total Revenue', type: 'metric', category: 'kpi' },
    { id: 'kpi_patient_volume', name: 'Patient Volume', type: 'metric', category: 'kpi' },
    { id: 'kpi_appointment_efficiency', name: 'Appointment Efficiency', type: 'metric', category: 'kpi' },
    { id: 'kpi_profit_margin', name: 'Profit Margin', type: 'metric', category: 'kpi' },
    { id: 'revenue_trends', name: 'Revenue Trends', type: 'chart', category: 'analytics' },
    { id: 'location_performance', name: 'Location Performance', type: 'chart', category: 'analytics' },
    { id: 'patient_acquisition', name: 'Patient Acquisition', type: 'chart', category: 'analytics' },
    { id: 'staff_productivity', name: 'Staff Productivity', type: 'chart', category: 'analytics' },
  ];
  res.json({ success: true, widgets });
});

export default router;
