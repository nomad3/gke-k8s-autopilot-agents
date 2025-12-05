import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { practiceAPI } from '../../services/api';
import type { Practice } from '../../store/authStore';

const PracticesPage: React.FC = () => {
  const { data, isLoading, error } = useQuery<{ practices: Practice[] }, Error>({
    queryKey: ['practices'],
    queryFn: () => practiceAPI.getPractices(),
  });

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Practice Management</h1>
      <div className="bg-white rounded-lg shadow border p-6">
        {isLoading && <p className="text-gray-600">Loading practices…</p>}
        {error && <p className="text-red-600">Failed to load practices</p>}
        {data?.practices?.length ? (
          <ul className="divide-y divide-gray-200">
            {data.practices.map((p) => (
              <li key={p.id} className="py-3">
                <div className="font-medium text-gray-900">{p.name}</div>
                <div className="text-sm text-gray-500">{p.address?.city || ''}</div>
              </li>
            ))}
          </ul>
        ) : !isLoading ? (
          <p className="text-gray-600">No practices found.</p>
        ) : null}
      </div>
    </div>
  );
};

export default PracticesPage;
