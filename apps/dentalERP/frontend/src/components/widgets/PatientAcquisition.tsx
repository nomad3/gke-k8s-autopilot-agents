import React from 'react';
import { usePatientAcquisition } from '../../hooks/useAnalytics';

const PatientAcquisition: React.FC = () => {
  const { data, error } = usePatientAcquisition('30d');
  const isBlank = !!error || !data?.data;
  const totals = isBlank ? { total: 0, referrals: 0, marketing: 0, walkIns: 0, trend: 'flat' } : data!.data;

  return (
    <div className="bg-white rounded-lg shadow border p-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">Patient Acquisition</h3>
          <p className="text-sm text-gray-600">New patient trends and conversion metrics</p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4 mb-4">
        <div className="text-center">
          <div className="text-2xl font-bold text-primary-600">{isBlank ? '—' : totals.total}</div>
          <div className="text-xs text-gray-500">New Patients</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-green-600">{isBlank ? '—' : totals.marketing}</div>
          <div className="text-xs text-gray-500">Marketing</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-blue-600">{isBlank ? '—' : totals.referrals}</div>
          <div className="text-xs text-gray-500">Referrals</div>
        </div>
      </div>

      <div className="space-y-2 mb-4">
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Walk-ins:</span>
          <span className="font-semibold text-gray-900">{isBlank ? '—' : totals.walkIns}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-600">Trend:</span>
          <span className="font-semibold text-gray-900">{isBlank ? '—' : totals.trend}</span>
        </div>
      </div>

      <div className="text-xs text-gray-500">
        📊 Data from DentalIntel marketing analytics and Dentrix patient records
      </div>
    </div>
  );
};

export default PatientAcquisition;
