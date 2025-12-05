import React, { useState } from 'react';
import { useAuthStore } from '../../store/authStore';

interface ReportConfig {
  type: 'executive' | 'financial' | 'operational' | 'clinical';
  dateRange: string;
  practiceIds: string[];
  format: 'pdf' | 'excel' | 'csv';
  metrics: string[];
}

const ReportGenerator: React.FC = () => {
  const user = useAuthStore(state => state.user);
  const [reportConfig, setReportConfig] = useState<ReportConfig>({
    type: 'executive',
    dateRange: '30d',
    practiceIds: user?.practiceIds || [],
    format: 'pdf',
    metrics: ['revenue', 'patients', 'efficiency']
  });
  const [generating, setGenerating] = useState(false);

  const reportTypes = {
    executive: {
      name: 'Executive Summary',
      description: 'High-level KPIs and strategic insights',
      metrics: ['revenue', 'patients', 'efficiency', 'profitMargin', 'locationPerformance']
    },
    financial: {
      name: 'Financial Performance',
      description: 'Revenue analysis and financial metrics',
      metrics: ['revenue', 'profitMargin', 'collections', 'expenses', 'roi']
    },
    operational: {
      name: 'Operational Analytics',
      description: 'Daily operations and staff productivity',
      metrics: ['appointments', 'efficiency', 'staffProductivity', 'utilization']
    },
    clinical: {
      name: 'Clinical Outcomes',
      description: 'Treatment success rates and clinical metrics',
      metrics: ['treatmentSuccess', 'patientSatisfaction', 'clinicalEfficiency']
    }
  };

  const handleGenerateReport = async () => {
    setGenerating(true);

    try {
      // Simulate report generation
      await new Promise(resolve => setTimeout(resolve, 3000));

      // In production, this would call:
      // const response = await api.post('/reports/generate', reportConfig);
      // downloadFile(response.data.downloadUrl);

      console.log('Generated report:', reportConfig);
      alert(`${reportTypes[reportConfig.type].name} report generated successfully!`);

    } catch (error) {
      console.error('Report generation failed:', error);
      alert('Report generation failed. Please try again.');
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow border p-6">
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-gray-900">BI Report Generator</h3>
        <p className="text-sm text-gray-600">Generate comprehensive business intelligence reports</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Report Configuration */}
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Report Type</label>
            <select
              value={reportConfig.type}
              onChange={(e) => setReportConfig({ ...reportConfig, type: e.target.value as any })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
            >
              {Object.entries(reportTypes).map(([key, report]) => (
                <option key={key} value={key}>{report.name}</option>
              ))}
            </select>
            <p className="text-xs text-gray-500 mt-1">
              {reportTypes[reportConfig.type].description}
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Date Range</label>
            <select
              value={reportConfig.dateRange}
              onChange={(e) => setReportConfig({ ...reportConfig, dateRange: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="7d">Last 7 Days</option>
              <option value="30d">Last 30 Days</option>
              <option value="90d">Last 90 Days</option>
              <option value="12m">Last 12 Months</option>
              <option value="ytd">Year to Date</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Export Format</label>
            <div className="flex space-x-4">
              {(['pdf', 'excel', 'csv'] as const).map((format) => (
                <label key={format} className="flex items-center">
                  <input
                    type="radio"
                    name="format"
                    value={format}
                    checked={reportConfig.format === format}
                    onChange={(e) => setReportConfig({ ...reportConfig, format: e.target.value as any })}
                    className="text-primary-600 focus:ring-primary-500"
                  />
                  <span className="ml-2 text-sm text-gray-700 uppercase">{format}</span>
                </label>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Include Metrics</label>
            <div className="space-y-2">
              {reportTypes[reportConfig.type].metrics.map((metric) => (
                <label key={metric} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={reportConfig.metrics.includes(metric)}
                    onChange={(e) => {
                      const metrics = e.target.checked
                        ? [...reportConfig.metrics, metric]
                        : reportConfig.metrics.filter(m => m !== metric);
                      setReportConfig({ ...reportConfig, metrics });
                    }}
                    className="text-primary-600 focus:ring-primary-500"
                  />
                  <span className="ml-2 text-sm text-gray-700 capitalize">{metric.replace(/([A-Z])/g, ' $1')}</span>
                </label>
              ))}
            </div>
          </div>
        </div>

        {/* Report Preview */}
        <div className="border border-gray-200 rounded-lg p-4">
          <h4 className="font-medium text-gray-900 mb-3">Report Preview</h4>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Type:</span>
              <span className="font-medium">{reportTypes[reportConfig.type].name}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Period:</span>
              <span className="font-medium">{reportConfig.dateRange}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Practices:</span>
              <span className="font-medium">{reportConfig.practiceIds.length} locations</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Format:</span>
              <span className="font-medium uppercase">{reportConfig.format}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Metrics:</span>
              <span className="font-medium">{reportConfig.metrics.length} selected</span>
            </div>
          </div>

          <div className="mt-4 pt-4 border-t border-gray-100">
            <h5 className="text-sm font-medium text-gray-900 mb-2">Data Sources</h5>
            <div className="space-y-1 text-xs text-gray-600">
              <div>📊 DentalIntel: Analytics and benchmarks</div>
              <div>🦷 Dentrix: Patient and appointment data</div>
              <div>💰 Eaglesoft: Financial and billing data</div>
              <div>💼 ADP: Staff productivity metrics</div>
            </div>
          </div>
        </div>
      </div>

      {/* Generate Button */}
      <div className="mt-6 pt-6 border-t border-gray-100">
        <button
          onClick={handleGenerateReport}
          disabled={generating || reportConfig.metrics.length === 0}
          className="w-full px-6 py-3 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {generating ? (
            <div className="flex items-center justify-center">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Generating Report...
            </div>
          ) : (
            `📄 Generate ${reportTypes[reportConfig.type].name}`
          )}
        </button>
      </div>

      {/* Scheduled Reports */}
      <div className="mt-6 pt-6 border-t border-gray-100">
        <h4 className="font-medium text-gray-900 mb-3">Scheduled Reports</h4>
        <div className="space-y-2">
          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div>
              <div className="text-sm font-medium text-gray-900">Weekly Executive Summary</div>
              <div className="text-xs text-gray-600">Every Monday at 8:00 AM</div>
            </div>
            <div className="text-xs text-green-600">Active</div>
          </div>
          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div>
              <div className="text-sm font-medium text-gray-900">Monthly Financial Report</div>
              <div className="text-xs text-gray-600">First of month at 9:00 AM</div>
            </div>
            <div className="text-xs text-green-600">Active</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReportGenerator;
