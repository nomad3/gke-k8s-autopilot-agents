import React, { useState } from 'react';
import {
  KeyIcon,
  PlusIcon,
  TrashIcon,
  EyeIcon,
  EyeSlashIcon,
  ClipboardDocumentIcon,
  CheckIcon,
} from '@heroicons/react/24/outline';

export interface APIKey {
  id: string;
  name: string;
  key: string;
  created_at: string;
  last_used?: string;
  status: 'active' | 'revoked';
}

export interface APIKeyManagerProps {
  tenantId: string;
  apiKeys: APIKey[];
  onCreateKey: (name: string) => Promise<APIKey>;
  onRevokeKey: (keyId: string) => Promise<void>;
  loading?: boolean;
}

/**
 * APIKeyManager - Manage API keys for tenant access
 * Features: Create/revoke keys, copy to clipboard, show/hide keys, last used timestamps
 */
export const APIKeyManager: React.FC<APIKeyManagerProps> = ({
  apiKeys,
  onCreateKey,
  onRevokeKey,
  loading = false,
}) => {
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newKeyName, setNewKeyName] = useState('');
  const [creating, setCreating] = useState(false);
  const [visibleKeys, setVisibleKeys] = useState<Set<string>>(new Set());
  const [copiedKeys, setCopiedKeys] = useState<Set<string>>(new Set());
  const [revoking, setRevoking] = useState<string | null>(null);

  const handleCreate = async () => {
    if (!newKeyName.trim()) return;

    setCreating(true);
    try {
      await onCreateKey(newKeyName);
      setNewKeyName('');
      setShowCreateForm(false);
    } catch (error) {
      console.error('Failed to create API key:', error);
    } finally {
      setCreating(false);
    }
  };

  const handleRevoke = async (keyId: string) => {
    setRevoking(keyId);
    try {
      await onRevokeKey(keyId);
    } catch (error) {
      console.error('Failed to revoke API key:', error);
    } finally {
      setRevoking(null);
    }
  };

  const toggleVisibility = (keyId: string) => {
    setVisibleKeys(prev => {
      const newSet = new Set(prev);
      if (newSet.has(keyId)) {
        newSet.delete(keyId);
      } else {
        newSet.add(keyId);
      }
      return newSet;
    });
  };

  const copyToClipboard = async (keyId: string, key: string) => {
    try {
      await navigator.clipboard.writeText(key);
      setCopiedKeys(prev => new Set(prev).add(keyId));
      setTimeout(() => {
        setCopiedKeys(prev => {
          const newSet = new Set(prev);
          newSet.delete(keyId);
          return newSet;
        });
      }, 2000);
    } catch (error) {
      console.error('Failed to copy to clipboard:', error);
    }
  };

  const maskKey = (key: string) => {
    if (key.length <= 8) return '••••••••';
    return `${key.substring(0, 4)}••••••••${key.substring(key.length - 4)}`;
  };

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return 'Never';
    const date = new Date(dateStr);
    return date.toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <KeyIcon className="w-8 h-8 text-orange-600 dark:text-orange-400" />
          <div>
            <h3 className="text-lg font-bold text-gray-900 dark:text-white">
              API Keys
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Manage authentication keys for this tenant
            </p>
          </div>
        </div>

        {!showCreateForm && (
          <button
            onClick={() => setShowCreateForm(true)}
            className="flex items-center space-x-2 px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white rounded-lg transition-colors text-sm font-medium"
          >
            <PlusIcon className="w-4 h-4" />
            <span>Create Key</span>
          </button>
        )}
      </div>

      {/* Create Form */}
      {showCreateForm && (
        <div className="mb-6 p-4 bg-orange-50 dark:bg-orange-900/20 rounded-lg border border-orange-200 dark:border-orange-800 animate-in slide-in-from-top-2 duration-200">
          <label className="block text-sm font-medium text-orange-900 dark:text-orange-100 mb-2">
            Key Name
          </label>
          <div className="flex items-center space-x-3">
            <input
              type="text"
              value={newKeyName}
              onChange={(e) => setNewKeyName(e.target.value)}
              className="flex-1 px-4 py-2 border border-orange-300 dark:border-orange-700 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
              placeholder="e.g., Production API Key"
              onKeyPress={(e) => e.key === 'Enter' && handleCreate()}
            />
            <button
              onClick={handleCreate}
              disabled={creating || !newKeyName.trim()}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                creating || !newKeyName.trim()
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-orange-600 hover:bg-orange-700 text-white'
              }`}
            >
              {creating ? 'Creating...' : 'Create'}
            </button>
            <button
              onClick={() => {
                setShowCreateForm(false);
                setNewKeyName('');
              }}
              className="px-4 py-2 bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg transition-colors text-sm font-medium"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* API Keys List */}
      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map(i => (
            <div key={i} className="animate-pulse">
              <div className="h-20 bg-gray-200 dark:bg-gray-700 rounded-lg"></div>
            </div>
          ))}
        </div>
      ) : apiKeys.length === 0 ? (
        <div className="text-center py-12">
          <KeyIcon className="w-12 h-12 text-gray-400 dark:text-gray-600 mx-auto mb-3" />
          <p className="text-gray-500 dark:text-gray-400 text-sm">
            No API keys created yet
          </p>
          <p className="text-gray-400 dark:text-gray-500 text-xs mt-1">
            Create a key to start accessing the API
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {apiKeys.map((apiKey) => {
            const isVisible = visibleKeys.has(apiKey.id);
            const isCopied = copiedKeys.has(apiKey.id);
            const isRevoked = apiKey.status === 'revoked';

            return (
              <div
                key={apiKey.id}
                className={`p-4 rounded-lg border transition-all ${
                  isRevoked
                    ? 'bg-gray-50 dark:bg-gray-750 border-gray-300 dark:border-gray-600 opacity-60'
                    : 'bg-gradient-to-br from-orange-50 to-amber-50 dark:from-orange-900/10 dark:to-amber-900/10 border-orange-200 dark:border-orange-800 hover:shadow-md'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    {/* Key Name & Status */}
                    <div className="flex items-center space-x-3 mb-2">
                      <h4 className="text-sm font-semibold text-gray-900 dark:text-white">
                        {apiKey.name}
                      </h4>
                      <span
                        className={`px-2 py-0.5 text-xs rounded-full ${
                          isRevoked
                            ? 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
                            : 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
                        }`}
                      >
                        {isRevoked ? 'Revoked' : 'Active'}
                      </span>
                    </div>

                    {/* Key Value */}
                    <div className="flex items-center space-x-2 mb-3">
                      <code className="flex-1 px-3 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded text-xs font-mono text-gray-900 dark:text-white">
                        {isVisible ? apiKey.key : maskKey(apiKey.key)}
                      </code>

                      {/* Toggle Visibility */}
                      <button
                        onClick={() => toggleVisibility(apiKey.id)}
                        className="p-2 hover:bg-white dark:hover:bg-gray-800 rounded transition-colors"
                        title={isVisible ? 'Hide key' : 'Show key'}
                      >
                        {isVisible ? (
                          <EyeSlashIcon className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                        ) : (
                          <EyeIcon className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                        )}
                      </button>

                      {/* Copy to Clipboard */}
                      <button
                        onClick={() => copyToClipboard(apiKey.id, apiKey.key)}
                        className="p-2 hover:bg-white dark:hover:bg-gray-800 rounded transition-colors"
                        title="Copy to clipboard"
                      >
                        {isCopied ? (
                          <CheckIcon className="w-4 h-4 text-green-600 dark:text-green-400" />
                        ) : (
                          <ClipboardDocumentIcon className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                        )}
                      </button>
                    </div>

                    {/* Metadata */}
                    <div className="flex items-center space-x-4 text-xs text-gray-600 dark:text-gray-400">
                      <span>Created: {formatDate(apiKey.created_at)}</span>
                      {apiKey.last_used && (
                        <span>Last used: {formatDate(apiKey.last_used)}</span>
                      )}
                    </div>
                  </div>

                  {/* Revoke Button */}
                  {!isRevoked && (
                    <button
                      onClick={() => handleRevoke(apiKey.id)}
                      disabled={revoking === apiKey.id}
                      className={`ml-4 p-2 rounded-lg transition-colors ${
                        revoking === apiKey.id
                          ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                          : 'hover:bg-red-100 dark:hover:bg-red-900/30 text-red-600 dark:text-red-400'
                      }`}
                      title="Revoke key"
                    >
                      <TrashIcon className="w-5 h-5" />
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Security Warning */}
      <div className="mt-6 p-4 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg border border-yellow-200 dark:border-yellow-800">
        <div className="flex items-start space-x-3">
          <span className="text-yellow-600 dark:text-yellow-400 text-xl">⚠️</span>
          <div>
            <div className="text-sm font-semibold text-yellow-900 dark:text-yellow-100">
              Security Best Practices
            </div>
            <ul className="text-sm text-yellow-700 dark:text-yellow-300 mt-2 space-y-1 list-disc list-inside">
              <li>Never share API keys in public repositories or insecure channels</li>
              <li>Rotate keys regularly and revoke unused keys immediately</li>
              <li>Use environment variables to store keys in production</li>
              <li>Monitor the "Last used" timestamp for suspicious activity</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};
