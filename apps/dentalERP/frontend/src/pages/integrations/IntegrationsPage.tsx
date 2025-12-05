import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { LoadingSpinner } from '../../components/ui/LoadingSpinner';
import { useIntegrationStatus } from '../../hooks/useAnalytics';
import { useIntegrationCredentialMutations, useIntegrationCredentialSummaries } from '../../hooks/useIntegrations';
import { integrationCredentialsAPI } from '../../services/api';
import { useAuthStore } from '../../store/authStore';

type TemplateField = {
  key: string;
  label: string;
  placeholder?: string;
  helperText?: string;
  defaultValue?: string;
  required?: boolean;
};

type IntegrationTemplate = {
  displayName: string;
  credentials: TemplateField[];
  metadata?: TemplateField[];
};

type FormEntry = {
  id: string;
  key: string;
  value: string;
  label?: string;
  placeholder?: string;
  helperText?: string;
  required?: boolean;
};

type CredentialFormValues = {
  practiceId: string;
  integrationType: string;
  name: string;
  credentials: FormEntry[];
  metadata: FormEntry[];
};

const integrationTemplates: Record<string, IntegrationTemplate> = {
  netsuite: {
    displayName: 'NetSuite',
    credentials: [
      { key: 'apiUrl', label: 'API Base URL', placeholder: 'https://123456-sb1.suitetalk.api.netsuite.com/services/rest/record/v1/' },
      { key: 'account', label: 'Account ID', placeholder: '123456_SB1' },
      { key: 'consumerKey', label: 'Consumer Key' },
      { key: 'consumerSecret', label: 'Consumer Secret' },
      { key: 'tokenKey', label: 'Token ID' },
      { key: 'tokenSecret', label: 'Token Secret' },
    ],
    metadata: [
      { key: 'endpoints.transactions', label: 'Transactions Endpoint', defaultValue: 'record/v1/journalEntry' },
      { key: 'query.transactions.sort', label: 'Sort Order', defaultValue: 'lastModifiedDate:DESC' },
      { key: 'query.transactions.fields', label: 'Fields CSV', defaultValue: 'internalId,tranId,tranDate,postingPeriod,subsidiary,entity,amount,currency,status,memo,createdDate,lastModifiedDate', helperText: 'Comma-separated field list returned from NetSuite.' },
    ],
  },
  snowflake: {
    displayName: 'Snowflake',
    credentials: [
      { key: 'account', label: 'Account' },
      { key: 'username', label: 'Username' },
      { key: 'password', label: 'Password' },
      { key: 'warehouse', label: 'Warehouse' },
      { key: 'database', label: 'Database' },
      { key: 'schema', label: 'Schema' },
      { key: 'role', label: 'Role' },
      { key: 'region', label: 'Region', placeholder: 'us-east-1' },
    ],
    metadata: [
      { key: 'stage', label: 'Stage Name', placeholder: '@NETSUITE_STAGE' },
    ],
  },
  dentrix: {
    displayName: 'Dentrix',
    credentials: [
      { key: 'apiUrl', label: 'API URL' },
      { key: 'clientId', label: 'Client ID' },
      { key: 'clientSecret', label: 'Client Secret' },
    ],
  },
  dentalintel: {
    displayName: 'DentalIntel',
    credentials: [
      { key: 'apiUrl', label: 'API URL' },
      { key: 'apiKey', label: 'API Key' },
    ],
  },
  adp: {
    displayName: 'ADP',
    credentials: [
      { key: 'apiUrl', label: 'API URL' },
      { key: 'clientId', label: 'Client ID' },
      { key: 'clientSecret', label: 'Client Secret' },
    ],
  },
  eaglesoft: {
    displayName: 'Eaglesoft',
    credentials: [
      { key: 'apiUrl', label: 'API URL' },
      { key: 'username', label: 'Username' },
      { key: 'password', label: 'Password' },
    ],
  },
};

const generateEntryId = () => Math.random().toString(36).slice(2, 10);

const createEntryFromField = (field: TemplateField): FormEntry => ({
  id: generateEntryId(),
  key: field.key,
  value: field.defaultValue ?? '',
  label: field.label,
  placeholder: field.placeholder,
  helperText: field.helperText,
  required: field.required,
});

const createEmptyEntry = (): FormEntry => ({
  id: generateEntryId(),
  key: '',
  value: '',
});

const getTemplate = (integrationType: string): IntegrationTemplate | undefined => {
  if (!integrationType) return undefined;
  return integrationTemplates[integrationType.toLowerCase()];
};

const flattenObjectToEntries = (input: Record<string, unknown> | undefined): FormEntry[] => {
  const entries: FormEntry[] = [];
  const walk = (obj: Record<string, unknown>, parentKey = ''): void => {
    Object.entries(obj).forEach(([key, value]) => {
      const fullKey = parentKey ? `${parentKey}.${key}` : key;
      if (value && typeof value === 'object' && !Array.isArray(value)) {
        walk(value as Record<string, unknown>, fullKey);
      } else {
        entries.push({
          id: generateEntryId(),
          key: fullKey,
          value: value === undefined || value === null ? '' : String(value),
        });
      }
    });
  };

  if (input && typeof input === 'object') {
    walk(input as Record<string, unknown>);
  }

  return entries;
};

const mergeTemplateIntoEntries = (
  entries: FormEntry[],
  templateFields?: TemplateField[],
): FormEntry[] => {
  if (!templateFields || templateFields.length === 0) {
    return entries.length ? entries : [createEmptyEntry()];
  }

  const templateMap = new Map(templateFields.map((field) => [field.key, field]));
  const hydratedEntries = entries.map((entry) => {
    const template = templateMap.get(entry.key);
    if (!template) return entry;
    return {
      ...entry,
      label: template.label,
      placeholder: template.placeholder,
      helperText: template.helperText,
      required: template.required,
    };
  });

  templateFields.forEach((field) => {
    const exists = hydratedEntries.some((entry) => entry.key === field.key);
    if (!exists) {
      hydratedEntries.push(createEntryFromField(field));
    }
  });

  return hydratedEntries.length ? hydratedEntries : [createEmptyEntry()];
};

const entriesToNestedObject = (entries: FormEntry[], parseValues: boolean): Record<string, unknown> => {
  const result: Record<string, any> = {};

  entries.forEach(({ key, value }) => {
    const trimmedKey = key.trim();
    if (!trimmedKey) return;
    const path = trimmedKey.split('.');
    let cursor = result;

    path.forEach((segment, index) => {
      if (!segment) return;
      if (index === path.length - 1) {
        cursor[segment] = parseValues ? parseMetadataValue(value) : value;
      } else {
        if (typeof cursor[segment] !== 'object' || cursor[segment] === null) {
          cursor[segment] = {};
        }
        cursor = cursor[segment];
      }
    });
  });

  return pruneEmptyValues(result);
};

const parseMetadataValue = (raw: string): unknown => {
  const trimmed = raw.trim();
  if (!trimmed.length) return '';
  if (trimmed === 'true' || trimmed === 'false') return trimmed === 'true';
  if (!Number.isNaN(Number(trimmed)) && trimmed === String(Number(trimmed))) {
    return Number(trimmed);
  }
  if ((trimmed.startsWith('{') && trimmed.endsWith('}')) || (trimmed.startsWith('[') && trimmed.endsWith(']'))) {
    try {
      return JSON.parse(trimmed);
    } catch {
      return trimmed;
    }
  }
  return trimmed;
};

const pruneEmptyValues = (obj: Record<string, unknown>): Record<string, unknown> => {
  Object.keys(obj).forEach((key) => {
    const value = obj[key];
    if (value && typeof value === 'object' && !Array.isArray(value)) {
      const cleaned = pruneEmptyValues(value as Record<string, unknown>);
      if (!Object.keys(cleaned).length) {
        delete obj[key];
      } else {
        obj[key] = cleaned;
      }
    } else if (value === '' || value === undefined || value === null) {
      delete obj[key];
    }
  });
  return obj;
};

const hasOnlyEmptyEntry = (entries: FormEntry[]): boolean => {
  if (entries.length === 0) return true;
  if (entries.length > 1) return false;
  const [entry] = entries;
  if (!entry) return true;
  return !entry.key.trim() && !entry.value.trim();
};

const IntegrationsPage: React.FC = () => {
  const { data: integrationData, isLoading, error, refetch } = useIntegrationStatus();
  const user = useAuthStore((state) => state.user);
  const practices = useAuthStore((state) => state.practices);
  const currentPractice = useAuthStore((state) => state.currentPractice);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState<'create' | 'edit'>('create');
  const [formValues, setFormValues] = useState<CredentialFormValues>({
    practiceId: currentPractice?.id ?? '',
    integrationType: '',
    name: '',
    credentials: [],
    metadata: [],
  });
  const [formError, setFormError] = useState<string | null>(null);
  const [modalBusy, setModalBusy] = useState(false);
  const [testingConnection, setTestingConnection] = useState<string | null>(null);

  useEffect(() => {
    if (isModalOpen && currentPractice?.id) {
      setFormValues((prev) => ({
        ...prev,
        practiceId: currentPractice.id,
      }));
    }
  }, [currentPractice?.id, isModalOpen]);

  useEffect(() => {
    if (!isModalOpen || modalMode !== 'create') return;
    setFormValues((prev) => {
      const template = getTemplate(prev.integrationType);
      const nextCredentials = template && hasOnlyEmptyEntry(prev.credentials)
        ? template.credentials.map(createEntryFromField)
        : prev.credentials;
      const nextMetadata = template && prev.metadata.length === 0
        ? (template.metadata?.map(createEntryFromField) ?? [])
        : prev.metadata;

      if (!template && hasOnlyEmptyEntry(prev.credentials)) {
        nextCredentials.push(createEmptyEntry());
      }

      return {
        ...prev,
        credentials: nextCredentials.length ? nextCredentials : [createEmptyEntry()],
        metadata: nextMetadata,
      };
    });
  }, [formValues.integrationType, isModalOpen, modalMode]);

  const isIntegrationAdmin = user?.role === 'admin' || user?.role === 'executive';
  const practiceFilterOptions = useMemo(() => {
    return practices.map((practice) => ({ value: practice.id, label: practice.name }));
  }, [practices]);

  const {
    data: credentialsResponse,
    isLoading: credentialsLoading,
    error: credentialsError,
    refetch: refetchCredentials,
  } = useIntegrationCredentialSummaries(currentPractice?.id);

  const credentialSummaries = credentialsResponse?.credentials ?? [];
  const { upsert, remove } = useIntegrationCredentialMutations();

  // Create a map of integration types to check if they're configured
  const configuredIntegrations = useMemo(() => {
    const map = new Map<string, boolean>();
    credentialSummaries.forEach((cred: any) => {
      map.set(cred.integrationType, cred.hasCredentials);
    });
    return map;
  }, [credentialSummaries]);

  const credentialsErrorMessage = useMemo(() => {
    if (!credentialsError) return null;
    if (credentialsError instanceof Error) return credentialsError.message;
    return 'Failed to load credentials.';
  }, [credentialsError]);

  const closeModal = () => {
    setIsModalOpen(false);
    setFormError(null);
    setModalBusy(false);
  };

  const populateFormFromDetail = (detail: any) => {
    const template = getTemplate(detail.integrationType);
    const credentialEntries = mergeTemplateIntoEntries(
      flattenObjectToEntries(detail.credentials),
      template?.credentials,
    );
    const metadataEntries = mergeTemplateIntoEntries(
      flattenObjectToEntries(detail.metadata),
      template?.metadata,
    );
    setFormValues({
      practiceId: detail.practiceId,
      integrationType: detail.integrationType,
      name: detail.name,
      credentials: credentialEntries,
      metadata: metadataEntries,
    });
  };

  const openEditModal = async (integrationType: string) => {
    if (!currentPractice?.id) {
      setFormError('Please select a practice first');
      return;
    }

    setModalMode('edit');
    setFormError(null);
    setModalBusy(true);
    setIsModalOpen(true);
    try {
      const response = await integrationCredentialsAPI.getCredential(currentPractice.id, integrationType);
      if (!response?.credential) {
        throw new Error('Credential not found');
      }
      populateFormFromDetail(response.credential);
    } catch (err) {
      const maybeStatus = (err as any)?.response?.status;
      if (maybeStatus === 404) {
        const template = getTemplate(integrationType);
        setModalMode('create');
        setFormValues({
          practiceId: currentPractice.id,
          integrationType,
          name: template?.displayName ?? '',
          credentials: template?.credentials?.map(createEntryFromField) ?? [createEmptyEntry()],
          metadata: template?.metadata?.map(createEntryFromField) ?? [],
        });
        setFormError('No credentials configured yet. Set up this integration below.');
      } else {
        setFormError(err instanceof Error ? err.message : 'Failed to load credential');
      }
    } finally {
      setModalBusy(false);
    }
  };

  const handleIntegrationCardClick = (integrationType: string) => {
    void openEditModal(integrationType);
  };

  const handleTestConnection = async (integrationType: string) => {
    if (!currentPractice?.id) {
      alert('Please select a practice first');
      return;
    }
    setTestingConnection(integrationType);
    try {
      const response = await integrationCredentialsAPI.testConnection(currentPractice.id, integrationType);
      if (response.success) {
        alert(`✓ Connection test successful!\n\n${integrationTemplates[integrationType]?.displayName || integrationType} is properly configured and responding.`);
      } else {
        alert(`✗ Connection test failed\n\n${response.error || 'Unknown error'}`);
      }
    } catch (err: any) {
      const errorMessage = err?.response?.data?.error || err.message || 'Unknown error';
      alert(`✗ Connection test failed\n\n${errorMessage}`);
    } finally {
      setTestingConnection(null);
    }
  };

  const handleSubmit: React.FormEventHandler<HTMLFormElement> = async (event) => {
    event.preventDefault();
    setFormError(null);

    const practiceId = formValues.practiceId.trim();
    const integrationType = formValues.integrationType.trim();
    const name = formValues.name.trim();

    if (!practiceId || !integrationType || !name) {
      setFormError('Practice, integration type, and name are required.');
      return;
    }

    const credentialKeys = new Set<string>();
    const credentialPayloadObject: Record<string, string> = {};
    for (const entry of formValues.credentials) {
      const key = entry.key.trim();
      if (!key) continue;
      if (credentialKeys.has(key)) {
        setFormError(`Duplicate credential key "${key}".`);
        return;
      }
      credentialKeys.add(key);
      credentialPayloadObject[key] = entry.value;
    }

    if (!Object.keys(credentialPayloadObject).length) {
      setFormError('Add at least one credential field.');
      return;
    }

    const metadataKeys = new Set<string>();
    for (const entry of formValues.metadata) {
      const key = entry.key.trim();
      if (!key) continue;
      if (metadataKeys.has(key)) {
        setFormError(`Duplicate metadata key "${key}".`);
        return;
      }
      metadataKeys.add(key);
    }

    const metadataPayloadObject = entriesToNestedObject(formValues.metadata, true);
    const metadataPayload = Object.keys(metadataPayloadObject).length ? metadataPayloadObject : undefined;

    setModalBusy(true);
    try {
      await upsert.mutateAsync({
        practiceId,
        integrationType,
        name,
        credentials: credentialPayloadObject,
        metadata: metadataPayload,
      });
      closeModal();
      void refetchCredentials();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to save credential');
      setModalBusy(false);
    }
  };

  const handleDelete = async (practiceId: string, integrationType: string) => {
    const confirmed = window.confirm('Delete stored credentials? This action cannot be undone.');
    if (!confirmed) {
      return;
    }
    try {
      await remove.mutateAsync({ practiceId, integrationType });
      void refetchCredentials();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : 'Failed to delete credential');
    }
  };

  if (isLoading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-64">
        <LoadingSpinner size="lg" />
        <span className="ml-3 text-gray-600">Loading integration status...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h3 className="text-red-800 font-medium">Unable to load integration status</h3>
          <p className="text-red-600 text-sm mt-1">Please check system connectivity.</p>
          <button
            onClick={() => refetch()}
            className="mt-2 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const systems = integrationData?.data || {};

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Integration Monitoring Dashboard</h1>
        <p className="text-gray-600">Real-time health monitoring for external dental software systems</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow border p-4 text-center">
          <div className="text-2xl font-bold text-green-600">{integrationData?.summary?.connected || 3}</div>
          <div className="text-sm text-gray-600">Connected</div>
        </div>
        <div className="bg-white rounded-lg shadow border p-4 text-center">
          <div className="text-2xl font-bold text-yellow-600">{integrationData?.summary?.syncing || 1}</div>
          <div className="text-sm text-gray-600">Syncing</div>
        </div>
        <div className="bg-white rounded-lg shadow border p-4 text-center">
          <div className="text-2xl font-bold text-red-600">{integrationData?.summary?.offline || 0}</div>
          <div className="text-sm text-gray-600">Offline</div>
        </div>
        <div className="bg-white rounded-lg shadow border p-4 text-center">
          <div className="text-2xl font-bold text-primary-600">{integrationData?.summary?.total || 4}</div>
          <div className="text-sm text-gray-600">Total Systems</div>
        </div>
      </div>

      {/* Integration Details */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {Object.entries(systems).map(([systemName, systemData]: [string, any]) => {
          const isConfigured = configuredIntegrations.get(systemName) ?? false;
          const statusColor = systemData.status === 'connected' ? 'green' :
                             systemData.status === 'syncing' ? 'yellow' : 'red';
          const statusIcon = systemData.status === 'connected' ? '🟢' :
                           systemData.status === 'syncing' ? '🟡' : '🔴';

          return (
            <div
              key={systemName}
              className="bg-white rounded-lg shadow border p-6 transition hover:shadow-lg relative cursor-pointer"
              onClick={() => handleIntegrationCardClick(systemName)}
            >
              {/* Configuration Status Badge */}
              {isConfigured && (
                <div className="absolute top-4 right-4">
                  <span className="inline-flex items-center px-2 py-1 text-xs font-medium text-green-700 bg-green-100 rounded-full">
                    ✓ Configured
                  </span>
                </div>
              )}

              {/* System Header */}
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <div className="text-2xl">{statusIcon}</div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 capitalize">{systemName}</h3>
                    <p className="text-sm text-gray-600 capitalize">{systemData.status}</p>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-medium text-gray-900">Uptime</div>
                  <div className={`text-sm text-${statusColor}-600`}>{systemData.uptime}</div>
                </div>
              </div>

              <div className="flex justify-end mb-4 gap-2">
                <button
                  type="button"
                  className={`px-3 py-1 text-sm font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 ${
                    isConfigured
                      ? 'text-white bg-primary-600 hover:bg-primary-700'
                      : 'text-primary-700 bg-primary-100 hover:bg-primary-200'
                  }`}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleIntegrationCardClick(systemName);
                  }}
                >
                  {isConfigured ? '⚙️ Configure' : '+ Connect'}
                </button>
              </div>

              {/* System Details */}
              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Last Sync:</span>
                  <span className="font-medium">
                    {new Date(systemData.lastSync).toLocaleTimeString()}
                  </span>
                </div>

                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Health:</span>
                  <span className={`font-medium text-${statusColor}-600 capitalize`}>
                    {systemData.health}
                  </span>
                </div>

                <div>
                  <div className="text-sm text-gray-600 mb-2">Data Points:</div>
                  <div className="flex flex-wrap gap-1">
                    {systemData.dataPoints.map((point: string) => (
                      <span
                        key={point}
                        className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-md"
                      >
                        {point}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="mt-4 pt-4 border-t border-gray-100 flex space-x-2">
                  <button
                    type="button"
                    className="px-3 py-1 text-xs bg-primary-100 text-primary-700 rounded-md hover:bg-primary-200 disabled:opacity-50"
                    onClick={(event) => {
                      event.stopPropagation();
                      void handleTestConnection(systemName);
                    }}
                    disabled={!isConfigured || testingConnection === systemName}
                  >
                    {testingConnection === systemName ? 'Testing...' : 'Test Connection'}
                  </button>
                  <button
                    type="button"
                    className="px-3 py-1 text-xs bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
                    onClick={(event) => {
                      event.stopPropagation();
                      // TODO: navigate to logs view when implemented
                    }}
                  >
                    View Logs
                  </button>
                </div>

                <div className="mt-4">
                  <Link
                    to={`/integrations/${systemName}`}
                    className="text-sm font-medium text-primary-600 hover:text-primary-700"
                    onClick={(event) => event.stopPropagation()}
                  >
                    View integration details →
                  </Link>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {isIntegrationAdmin && (
        <div className="bg-white rounded-lg shadow border p-6 space-y-4">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Configured Integrations</h2>
              <p className="text-sm text-gray-600">Manage encrypted credentials for {currentPractice?.name || 'this practice'}.</p>
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <button
                onClick={() => void refetchCredentials()}
                className="px-4 py-2 bg-gray-100 text-gray-800 text-sm rounded-md hover:bg-gray-200"
              >
                Refresh
              </button>
            </div>
          </div>

          {credentialsErrorMessage && (
            <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-md p-3">
              {credentialsErrorMessage}
            </div>
          )}

          {credentialsLoading ? (
            <div className="flex items-center space-x-3 text-gray-600">
              <LoadingSpinner size="sm" />
              <span>Loading credentials...</span>
            </div>
          ) : credentialSummaries.length === 0 ? (
            <div className="text-sm text-gray-600">No stored credentials found.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left font-medium text-gray-500 uppercase tracking-wider">Practice</th>
                    <th className="px-4 py-3 text-left font-medium text-gray-500 uppercase tracking-wider">Integration</th>
                    <th className="px-4 py-3 text-left font-medium text-gray-500 uppercase tracking-wider">Name</th>
                    <th className="px-4 py-3 text-left font-medium text-gray-500 uppercase tracking-wider">Fields</th>
                    <th className="px-4 py-3 text-left font-medium text-gray-500 uppercase tracking-wider">Updated</th>
                    <th className="px-4 py-3 text-right font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {credentialSummaries.map((credential: any) => {
                    const fieldPreview = credential.credentialKeys?.length
                      ? credential.credentialKeys.join(', ')
                      : '—';
                    const updatedAt = credential.updatedAt ? new Date(credential.updatedAt).toLocaleString() : '—';
                    const practiceName = practiceFilterOptions.find((option) => option.value === credential.practiceId)?.label || credential.practiceId;
                    return (
                      <tr key={`${credential.practiceId}-${credential.integrationType}`} className="hover:bg-gray-50">
                        <td className="px-4 py-3 text-gray-900">{practiceName}</td>
                        <td className="px-4 py-3 text-gray-900 capitalize">{credential.integrationType}</td>
                        <td className="px-4 py-3 text-gray-900">{credential.name}</td>
                        <td className="px-4 py-3 text-gray-600">{fieldPreview}</td>
                        <td className="px-4 py-3 text-gray-600">{updatedAt}</td>
                        <td className="px-4 py-3 flex justify-end gap-2">
                          <button
                            onClick={() => void openEditModal(credential.integrationType)}
                            className="px-3 py-1 bg-primary-100 text-primary-700 rounded-md hover:bg-primary-200"
                            disabled={modalBusy}
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => void handleDelete(credential.practiceId, credential.integrationType)}
                            className="px-3 py-1 bg-red-100 text-red-700 rounded-md hover:bg-red-200"
                            disabled={remove.isPending}
                          >
                            Delete
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Manual Ingestion CTA */}
      <div className="bg-white rounded-lg shadow border p-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Need data without a live integration?</h3>
            <p className="text-sm text-gray-600">Upload CSV or PDF and we’ll parse it.</p>
          </div>
          <Link to="/integrations/ingestion" className="px-4 py-2 bg-gray-100 text-gray-800 rounded-md hover:bg-gray-200">
            Manual Ingestion
          </Link>
        </div>
      </div>

      {/* BI Data Flow Visualization */}
      <div className="bg-white rounded-lg shadow border p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Business Intelligence Data Flow</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <div className="text-2xl mb-2">🦷</div>
            <div className="font-medium text-gray-900">Dentrix</div>
            <div className="text-xs text-gray-600 mt-1">Patient data → BI Analytics</div>
          </div>
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <div className="text-2xl mb-2">📊</div>
            <div className="font-medium text-gray-900">DentalIntel</div>
            <div className="text-xs text-gray-600 mt-1">Analytics → Executive KPIs</div>
          </div>
          <div className="text-center p-4 bg-yellow-50 rounded-lg">
            <div className="text-2xl mb-2">💼</div>
            <div className="font-medium text-gray-900">ADP</div>
            <div className="text-xs text-gray-600 mt-1">Staff data → Productivity metrics</div>
          </div>
          <div className="text-center p-4 bg-purple-50 rounded-lg">
            <div className="text-2xl mb-2">💰</div>
            <div className="font-medium text-gray-900">Eaglesoft</div>
            <div className="text-xs text-gray-600 mt-1">Financial data → Revenue analytics</div>
          </div>
        </div>
      </div>

      {/* Refresh Button */}
      <div className="text-center">
        <button
          onClick={() => refetch()}
          className="px-6 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 transition-colors"
        >
          🔄 Refresh All Integrations
        </button>
      </div>

      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-30 px-4">
          <div className="w-full max-w-2xl bg-white rounded-lg shadow-lg p-6 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between sticky top-0 bg-white pb-4 border-b">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">
                  {modalMode === 'edit' ? 'Configure Integration' : 'Connect Integration'}
                </h3>
                <p className="text-sm text-gray-600 mt-1">
                  {formValues.integrationType ? integrationTemplates[formValues.integrationType]?.displayName : ''}
                  {currentPractice?.name && ` • ${currentPractice.name}`}
                </p>
              </div>
              <button
                onClick={closeModal}
                className="text-gray-500 hover:text-gray-700"
                disabled={modalBusy}
              >
                ✕
              </button>
            </div>

            {formError && (
              <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 text-sm rounded-md p-3">
                {formError}
              </div>
            )}

            <form className="space-y-4" onSubmit={handleSubmit}>
              <div>
                <label className="block text-sm font-medium text-gray-700">Connection Name</label>
                <input
                  type="text"
                  value={formValues.name}
                  onChange={(event) => setFormValues((prev) => ({ ...prev, name: event.target.value }))}
                  className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                  placeholder="e.g., Production NetSuite"
                  disabled={modalBusy}
                  required
                />
                <p className="mt-1 text-xs text-gray-500">A friendly name to identify this connection</p>
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium text-gray-700">Authentication</label>
                  <button
                    type="button"
                    className="text-sm text-primary-600 hover:text-primary-700"
                    onClick={() =>
                      setFormValues((prev) => ({
                        ...prev,
                        credentials: [...prev.credentials, createEmptyEntry()],
                      }))
                    }
                    disabled={modalBusy}
                  >
                    + Add field
                  </button>
                </div>
                <p className="text-xs text-gray-500 mb-3">Enter your API credentials to connect this integration</p>
                <div className="space-y-3">
                  {formValues.credentials.map((entry) => (
                    <div key={entry.id} className="bg-gray-50 border border-gray-200 rounded-md p-4 space-y-3">
                      <div className="space-y-3">
                        <div>
                          <label className="block text-xs font-semibold text-gray-700 mb-1">
                            {entry.label || 'Field Name'}
                          </label>
                          <input
                            type="text"
                            value={entry.key}
                            onChange={(event) =>
                              setFormValues((prev) => ({
                                ...prev,
                                credentials: prev.credentials.map((item) =>
                                  item.id === entry.id ? { ...item, key: event.target.value } : item,
                                ),
                              }))
                            }
                            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                            placeholder="e.g., apiKey, clientId, account"
                            disabled={modalBusy || !!entry.label}
                          />
                        </div>
                        <div>
                          <label className="block text-xs font-semibold text-gray-700 mb-1">Value</label>
                          <input
                            type={entry.key.toLowerCase().includes('secret') || entry.key.toLowerCase().includes('password') ? 'password' : 'text'}
                            value={entry.value}
                            onChange={(event) =>
                              setFormValues((prev) => ({
                                ...prev,
                                credentials: prev.credentials.map((item) =>
                                  item.id === entry.id ? { ...item, value: event.target.value } : item,
                                ),
                              }))
                            }
                            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm font-mono"
                            placeholder={entry.placeholder || 'Enter value'}
                            disabled={modalBusy}
                          />
                        </div>
                      </div>
                      {entry.helperText && (
                        <p className="text-xs text-gray-500 italic">{entry.helperText}</p>
                      )}
                      <div className="flex justify-end pt-2 border-t border-gray-200">
                        <button
                          type="button"
                          className="text-xs text-red-600 hover:text-red-700 font-medium"
                          onClick={() =>
                            setFormValues((prev) => ({
                              ...prev,
                              credentials: prev.credentials.filter((item) => item.id !== entry.id),
                            }))
                          }
                          disabled={modalBusy || (formValues.credentials.length === 1 && hasOnlyEmptyEntry([entry]))}
                        >
                          Remove Field
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {formValues.metadata.length > 0 && (
                <div className="space-y-2 border-t pt-4">
                  <div className="flex items-center justify-between">
                    <label className="text-sm font-medium text-gray-700">Advanced Settings</label>
                    <button
                      type="button"
                      className="text-sm text-primary-600 hover:text-primary-700"
                      onClick={() =>
                        setFormValues((prev) => ({
                          ...prev,
                          metadata: [...prev.metadata, createEmptyEntry()],
                        }))
                      }
                      disabled={modalBusy}
                    >
                      + Add setting
                    </button>
                  </div>
                  <p className="text-xs text-gray-500 mb-3">Optional configuration for advanced use cases</p>
                  <div className="space-y-3">
                    {formValues.metadata.map((entry) => (
                      <div key={entry.id} className="bg-gray-50 border border-gray-200 rounded-md p-4 space-y-3">
                        <div className="space-y-3">
                          <div>
                            <label className="block text-xs font-semibold text-gray-700 mb-1">
                              {entry.label || 'Setting Name'}
                            </label>
                            <input
                              type="text"
                              value={entry.key}
                              onChange={(event) =>
                                setFormValues((prev) => ({
                                  ...prev,
                                  metadata: prev.metadata.map((item) =>
                                    item.id === entry.id ? { ...item, key: event.target.value } : item,
                                  ),
                                }))
                              }
                              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                              placeholder="e.g., query.transactions.sort"
                              disabled={modalBusy || !!entry.label}
                            />
                          </div>
                          <div>
                            <label className="block text-xs font-semibold text-gray-700 mb-1">Value</label>
                            <input
                              type="text"
                              value={entry.value}
                              onChange={(event) =>
                                setFormValues((prev) => ({
                                  ...prev,
                                  metadata: prev.metadata.map((item) =>
                                    item.id === entry.id ? { ...item, value: event.target.value } : item,
                                  ),
                                }))
                              }
                              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                              placeholder={entry.placeholder || 'Enter value'}
                              disabled={modalBusy}
                            />
                          </div>
                        </div>
                        {entry.helperText && (
                          <p className="text-xs text-gray-500 italic">{entry.helperText}</p>
                        )}
                        <div className="flex justify-end pt-2 border-t border-gray-200">
                          <button
                            type="button"
                            className="text-xs text-red-600 hover:text-red-700 font-medium"
                            onClick={() =>
                              setFormValues((prev) => ({
                                ...prev,
                                metadata: prev.metadata.filter((item) => item.id !== entry.id),
                              }))
                            }
                            disabled={modalBusy}
                          >
                            Remove Setting
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex items-center justify-end gap-3 pt-4 border-t sticky bottom-0 bg-white">
                <button
                  type="button"
                  onClick={closeModal}
                  className="px-6 py-2 text-sm text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
                  disabled={modalBusy}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-6 py-2 text-sm text-white bg-primary-600 rounded-md hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  disabled={modalBusy || upsert.isPending}
                >
                  {modalBusy || upsert.isPending ? (
                    <span className="flex items-center gap-2">
                      <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                      Saving...
                    </span>
                  ) : (
                    modalMode === 'edit' ? 'Save Changes' : 'Connect Integration'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default IntegrationsPage;
