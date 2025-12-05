import React, { useState } from 'react';
import { ArrowDownTrayIcon, DocumentTextIcon, TableCellsIcon, CheckCircleIcon } from '@heroicons/react/24/outline';

export interface ExportData {
  summary?: Record<string, any>;
  daily?: Array<Record<string, any>>;
  byPractice?: Array<Record<string, any>>;
  metadata?: {
    tenant?: string;
    dateRange?: string;
    generatedAt?: string;
  };
}

export interface AnalyticsExportProps {
  data: ExportData;
  filename?: string;
  disabled?: boolean;
}

/**
 * AnalyticsExport - Export analytics data to Excel (CSV) or PDF
 * Provides multi-format export with data transformation
 */
export const AnalyticsExport: React.FC<AnalyticsExportProps> = ({
  data,
  filename = 'analytics-export',
  disabled = false,
}) => {
  const [isExporting, setIsExporting] = useState(false);
  const [exportSuccess, setExportSuccess] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);

  // Format timestamp for filename
  const getTimestamp = () => {
    const now = new Date();
    return now.toISOString().split('T')[0];
  };

  // Export to CSV (Excel-compatible)
  const exportToCSV = () => {
    setIsExporting(true);

    try {
      const sections: string[] = [];

      // Add metadata header
      if (data.metadata) {
        sections.push('# Analytics Export Report');
        sections.push(`# Tenant: ${data.metadata.tenant || 'N/A'}`);
        sections.push(`# Date Range: ${data.metadata.dateRange || 'N/A'}`);
        sections.push(`# Generated: ${data.metadata.generatedAt || new Date().toISOString()}`);
        sections.push('');
      }

      // Add summary section
      if (data.summary) {
        sections.push('## Summary Metrics');
        sections.push('Metric,Value');
        Object.entries(data.summary).forEach(([key, value]) => {
          const formattedKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
          sections.push(`${formattedKey},${value}`);
        });
        sections.push('');
      }

      // Add by practice section
      if (data.byPractice && data.byPractice.length > 0) {
        sections.push('## Performance By Practice');
        const headers = Object.keys(data.byPractice[0] || {});
        sections.push(headers.join(','));
        data.byPractice.forEach(row => {
          const values = headers.map(h => {
            const val = row[h];
            // Escape commas and quotes in string values
            if (typeof val === 'string' && (val.includes(',') || val.includes('"'))) {
              return `"${val.replace(/"/g, '""')}"`;
            }
            return val;
          });
          sections.push(values.join(','));
        });
        sections.push('');
      }

      // Add daily data section
      if (data.daily && data.daily.length > 0) {
        sections.push('## Daily Production');
        const headers = Object.keys(data.daily[0] || {});
        sections.push(headers.join(','));
        data.daily.forEach(row => {
          const values = headers.map(h => {
            const val = row[h];
            if (typeof val === 'string' && (val.includes(',') || val.includes('"'))) {
              return `"${val.replace(/"/g, '""')}"`;
            }
            return val;
          });
          sections.push(values.join(','));
        });
      }

      const csvContent = sections.join('\n');
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      const url = URL.createObjectURL(blob);

      link.setAttribute('href', url);
      link.setAttribute('download', `${filename}-${getTimestamp()}.csv`);
      link.style.visibility = 'hidden';

      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);

      setExportSuccess(true);
      setTimeout(() => setExportSuccess(false), 3000);
    } catch (error) {
      console.error('CSV export failed:', error);
    } finally {
      setIsExporting(false);
      setShowDropdown(false);
    }
  };

  // Export to PDF (using HTML + Print API)
  const exportToPDF = () => {
    setIsExporting(true);

    try {
      // Create a new window with formatted content
      const printWindow = window.open('', '_blank');
      if (!printWindow) {
        throw new Error('Popup blocked - please allow popups for PDF export');
      }

      // Build HTML content
      let htmlContent = `
        <!DOCTYPE html>
        <html>
        <head>
          <title>${filename}</title>
          <style>
            body {
              font-family: Arial, sans-serif;
              padding: 20px;
              max-width: 1200px;
              margin: 0 auto;
            }
            h1 {
              color: #1e40af;
              border-bottom: 2px solid #1e40af;
              padding-bottom: 10px;
            }
            h2 {
              color: #3b82f6;
              margin-top: 30px;
              margin-bottom: 15px;
            }
            .metadata {
              background: #f3f4f6;
              padding: 15px;
              border-radius: 5px;
              margin-bottom: 20px;
            }
            .metadata p {
              margin: 5px 0;
              color: #4b5563;
            }
            table {
              width: 100%;
              border-collapse: collapse;
              margin-bottom: 30px;
            }
            th {
              background: #3b82f6;
              color: white;
              padding: 12px;
              text-align: left;
              font-weight: 600;
            }
            td {
              padding: 10px;
              border-bottom: 1px solid #e5e7eb;
            }
            tr:nth-child(even) {
              background: #f9fafb;
            }
            .summary-grid {
              display: grid;
              grid-template-columns: repeat(2, 1fr);
              gap: 15px;
              margin-bottom: 30px;
            }
            .summary-card {
              background: #f3f4f6;
              padding: 15px;
              border-radius: 5px;
            }
            .summary-card strong {
              color: #1e40af;
            }
            @media print {
              body { padding: 0; }
              h2 { page-break-before: always; }
              table { page-break-inside: avoid; }
            }
          </style>
        </head>
        <body>
          <h1>Analytics Export Report</h1>
      `;

      // Add metadata
      if (data.metadata) {
        htmlContent += `
          <div class="metadata">
            <p><strong>Tenant:</strong> ${data.metadata.tenant || 'N/A'}</p>
            <p><strong>Date Range:</strong> ${data.metadata.dateRange || 'N/A'}</p>
            <p><strong>Generated:</strong> ${data.metadata.generatedAt || new Date().toLocaleString()}</p>
          </div>
        `;
      }

      // Add summary
      if (data.summary) {
        htmlContent += '<h2>Summary Metrics</h2><div class="summary-grid">';
        Object.entries(data.summary).forEach(([key, value]) => {
          const formattedKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
          htmlContent += `
            <div class="summary-card">
              <strong>${formattedKey}:</strong><br/>
              ${value}
            </div>
          `;
        });
        htmlContent += '</div>';
      }

      // Add by practice table
      if (data.byPractice && data.byPractice.length > 0) {
        htmlContent += '<h2>Performance By Practice</h2><table>';
        const headers = Object.keys(data.byPractice[0] || {});
        htmlContent += '<thead><tr>';
        headers.forEach(h => {
          const formattedHeader = h.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
          htmlContent += `<th>${formattedHeader}</th>`;
        });
        htmlContent += '</tr></thead><tbody>';
        data.byPractice.forEach(row => {
          htmlContent += '<tr>';
          headers.forEach(h => {
            htmlContent += `<td>${row[h]}</td>`;
          });
          htmlContent += '</tr>';
        });
        htmlContent += '</tbody></table>';
      }

      // Add daily data table
      if (data.daily && data.daily.length > 0) {
        htmlContent += '<h2>Daily Production</h2><table>';
        const headers = Object.keys(data.daily[0] || {});
        htmlContent += '<thead><tr>';
        headers.forEach(h => {
          const formattedHeader = h.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
          htmlContent += `<th>${formattedHeader}</th>`;
        });
        htmlContent += '</tr></thead><tbody>';
        data.daily.forEach(row => {
          htmlContent += '<tr>';
          headers.forEach(h => {
            htmlContent += `<td>${row[h]}</td>`;
          });
          htmlContent += '</tr>';
        });
        htmlContent += '</tbody></table>';
      }

      htmlContent += '</body></html>';

      // Write content and trigger print
      printWindow.document.write(htmlContent);
      printWindow.document.close();

      // Wait for content to load, then print
      printWindow.onload = () => {
        printWindow.print();
      };

      setExportSuccess(true);
      setTimeout(() => setExportSuccess(false), 3000);
    } catch (error) {
      console.error('PDF export failed:', error);
      alert('PDF export failed. Please ensure popups are allowed.');
    } finally {
      setIsExporting(false);
      setShowDropdown(false);
    }
  };

  return (
    <div className="relative">
      {/* Main Export Button */}
      <button
        onClick={() => setShowDropdown(!showDropdown)}
        disabled={disabled || isExporting}
        className={`inline-flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
          disabled || isExporting
            ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
            : 'bg-sky-600 hover:bg-sky-700 text-white'
        }`}
      >
        {exportSuccess ? (
          <>
            <CheckCircleIcon className="w-5 h-5" />
            <span>Exported!</span>
          </>
        ) : (
          <>
            <ArrowDownTrayIcon className="w-5 h-5" />
            <span>{isExporting ? 'Exporting...' : 'Export'}</span>
          </>
        )}
      </button>

      {/* Dropdown Menu */}
      {showDropdown && !disabled && !isExporting && (
        <div className="absolute right-0 mt-2 w-56 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl z-50">
          <div className="py-2">
            {/* CSV Export Option */}
            <button
              onClick={exportToCSV}
              className="w-full px-4 py-3 text-left flex items-center space-x-3 hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors"
            >
              <TableCellsIcon className="w-5 h-5 text-green-600 dark:text-green-400" />
              <div>
                <div className="text-sm font-medium text-gray-900 dark:text-white">
                  Export to Excel
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  CSV format (.csv)
                </div>
              </div>
            </button>

            {/* PDF Export Option */}
            <button
              onClick={exportToPDF}
              className="w-full px-4 py-3 text-left flex items-center space-x-3 hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors border-t border-gray-200 dark:border-gray-700"
            >
              <DocumentTextIcon className="w-5 h-5 text-red-600 dark:text-red-400" />
              <div>
                <div className="text-sm font-medium text-gray-900 dark:text-white">
                  Export to PDF
                </div>
                <div className="text-xs text-gray-500 dark:text-gray-400">
                  Formatted report (.pdf)
                </div>
              </div>
            </button>
          </div>
        </div>
      )}

      {/* Click outside to close */}
      {showDropdown && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setShowDropdown(false)}
        />
      )}
    </div>
  );
};
