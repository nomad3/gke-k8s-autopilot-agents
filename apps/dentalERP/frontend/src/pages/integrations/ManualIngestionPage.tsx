            import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { ingestionAPI, practiceAPI } from '../../services/api';

type ManualIngestionStatus = 'stored' | 'delivered' | 'failed' | 'archived';

type ManualIngestionUpload = {
  id: string;
  practiceId: string;
  sourceSystem: string;
  dataset?: string | null;
  originalFilename: string;
  storagePath: string;
  status: ManualIngestionStatus;
  externalLocation?: string | null;
  notes?: string | null;
  createdAt?: string;
  updatedAt?: string;
};

type SupportedInfo = {
  maxFileSize?: number;
  allowedTypes?: string[];
  exportPath?: string;
  externalTarget?: string | null;
};

const statusOptions: ManualIngestionStatus[] = ['stored', 'delivered', 'failed', 'archived'];

const formatDateTime = (value?: string) => {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
};

const ManualIngestionPage: React.FC = () => {
  const [practices, setPractices] = useState<any[]>([]);
  const [practiceId, setPracticeId] = useState('');
  const [sourceSystem, setSourceSystem] = useState('manual-upload');
  const [dataset, setDataset] = useState('unknown');
  const [notes, setNotes] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploads, setUploads] = useState<ManualIngestionUpload[]>([]);
  const [loadingUploads, setLoadingUploads] = useState(false);
  const [supported, setSupported] = useState<SupportedInfo>({});
  const [feedback, setFeedback] = useState<string | null>(null);
  const [editingUpload, setEditingUpload] = useState<ManualIngestionUpload | null>(null);
  const [handoffStatus, setHandoffStatus] = useState<ManualIngestionStatus>('stored');
  const [handoffLocation, setHandoffLocation] = useState('');
  const [handoffNotes, setHandoffNotes] = useState('');
  const [handoffSaving, setHandoffSaving] = useState(false);

  const allowedTypesLabel = useMemo(() => {
    if (!supported.allowedTypes || !supported.allowedTypes.length) return 'Any file type';
    return supported.allowedTypes.join(', ');
  }, [supported.allowedTypes]);

  const loadUploads = useCallback(async () => {
    setLoadingUploads(true);
    try {
      const params = practiceId ? { practiceId } : undefined;
      const data = await ingestionAPI.listUploads(params);
      setUploads(Array.isArray(data?.uploads) ? data.uploads : []);
    } catch (error: any) {
      console.error('Failed to load manual ingestion uploads', error);
      setFeedback(`Failed to load uploads: ${error?.message || 'unknown error'}`);
    } finally {
      setLoadingUploads(false);
    }
  }, [practiceId]);

  useEffect(() => {
    (async () => {
      try {
        const [practiceResp, supportedResp] = await Promise.all([
          practiceAPI.getPractices(),
          ingestionAPI.getSupported(),
        ]);
        const practiceList = practiceResp?.practices || practiceResp || [];
        setPractices(practiceList);
        setSupported(supportedResp || {});
      } catch (error: any) {
        console.error('Failed to load manual ingestion config', error);
        setFeedback(`Failed to load config: ${error?.message || 'unknown error'}`);
      }
      await loadUploads();
    })();
  }, [loadUploads]);

  useEffect(() => {
    loadUploads().catch((error) => {
      console.error('Failed to refresh manual ingestion uploads', error);
    });
  }, [loadUploads]);

  const handleUpload = async (): Promise<void> => {
    if (!practiceId) {
      setFeedback('Select a practice before uploading.');
      return;
    }
    if (!sourceSystem) {
      setFeedback('Source system is required.');
      return;
    }
    if (!file) {
      setFeedback('Choose a file to upload.');
      return;
    }

    setUploading(true);
    setFeedback(null);
    try {
      const response = await ingestionAPI.upload({
        practiceId,
        sourceSystem,
        dataset: dataset || undefined,
        notes: notes || undefined,
        file,
      });

      if (response?.instructions) {
        setFeedback(response.instructions);
      } else {
        setFeedback('File uploaded for external processing.');
      }

      setFile(null);
      setNotes('');
      await loadUploads();
    } catch (error: any) {
      console.error('Manual ingestion upload failed', error);
      setFeedback(`Upload failed: ${error?.message || 'unknown error'}`);
    } finally {
      setUploading(false);
    }
  };

  const startHandoff = (upload: ManualIngestionUpload) => {
    setEditingUpload(upload);
    setHandoffStatus(upload.status);
    setHandoffLocation(upload.externalLocation || '');
    setHandoffNotes(upload.notes || '');
  };

  const cancelHandoff = () => {
    setEditingUpload(null);
    setHandoffSaving(false);
  };

  const submitHandoff = async (): Promise<void> => {
    if (!editingUpload) return;
    setHandoffSaving(true);
    try {
      await ingestionAPI.handoffUpload(editingUpload.id, {
        status: handoffStatus,
        externalLocation: handoffLocation || undefined,
        notes: handoffNotes || undefined,
      });
      setFeedback('Upload handoff updated.');
      await loadUploads();
      cancelHandoff();
    } catch (error: any) {
      console.error('Failed to update manual ingestion upload', error);
      setFeedback(`Update failed: ${error?.message || 'unknown error'}`);
    } finally {
      setHandoffSaving(false);
    }
  };

  const deleteUpload = async (uploadId: string): Promise<void> => {
    const confirmDelete = window.confirm('Remove this upload record? The stored file will also be removed if available.');
    if (!confirmDelete) return;
    try {
      await ingestionAPI.deleteUpload(uploadId);
      setFeedback('Upload deleted.');
      await loadUploads();
    } catch (error: any) {
      console.error('Failed to delete manual ingestion upload', error);
      setFeedback(`Delete failed: ${error?.message || 'unknown error'}`);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h1 className="text-2xl font-semibold text-gray-900">Manual Data Ingestion</h1>
        <button
          type="button"
          className="text-sm text-primary-600 hover:text-primary-700"
          onClick={() => loadUploads().catch(() => undefined)}
        >
          Refresh uploads
        </button>
      </div>

      {feedback && (
        <div className="border-l-4 border-primary-500 bg-primary-50 text-primary-800 px-4 py-2 text-sm rounded">
          {feedback}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow border p-6 space-y-4">
          <div>
            <h2 className="text-lg font-medium text-gray-900">Upload file</h2>
            <p className="text-sm text-gray-600 mt-1">
              Files are stored at `{supported.exportPath || 'uploads/manual-ingestion'}` and forwarded to
              {supported.externalTarget ? ` ${supported.externalTarget}.` : ' your external warehouse.'}
            </p>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm text-gray-700 mb-1" htmlFor="practiceId">Practice</label>
              <select
                id="practiceId"
                value={practiceId}
                onChange={(event) => setPracticeId(event.target.value)}
                className="w-full border rounded-md px-3 py-2"
              >
                <option value="">Select practice</option>
                {practices.map((practice: any) => (
                  <option key={practice.id} value={practice.id}>
                    {practice.name || practice.id}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm text-gray-700 mb-1" htmlFor="sourceSystem">Source system</label>
              <input
                id="sourceSystem"
                type="text"
                value={sourceSystem}
                onChange={(event) => setSourceSystem(event.target.value)}
                className="w-full border rounded-md px-3 py-2"
                placeholder="e.g. dentrix, adp, manual"
              />
            </div>

            <div>
              <label className="block text-sm text-gray-700 mb-1" htmlFor="dataset">Dataset</label>
              <input
                id="dataset"
                type="text"
                value={dataset}
                onChange={(event) => setDataset(event.target.value)}
                className="w-full border rounded-md px-3 py-2"
                placeholder="patients, payroll, financials, etc."
              />
            </div>

            <div>
              <label className="block text-sm text-gray-700 mb-1" htmlFor="notes">Notes (optional)</label>
              <textarea
                id="notes"
                value={notes}
                onChange={(event) => setNotes(event.target.value)}
                className="w-full border rounded-md px-3 py-2 min-h-[80px]"
                placeholder="Add context for the external team"
              />
            </div>

            <div>
              <label className="block text-sm text-gray-700 mb-1" htmlFor="fileInput">File</label>
              <input
                id="fileInput"
                type="file"
                onChange={(event) => setFile(event.target.files?.[0] || null)}
                className="w-full"
              />
              <p className="text-xs text-gray-500 mt-1">
                Allowed types: {allowedTypesLabel}. Max size: {supported.maxFileSize ? `${(supported.maxFileSize / (1024 * 1024)).toFixed(1)} MB` : '10 MB default'}.
              </p>
            </div>
          </div>

          <div className="pt-2">
            <button
              type="button"
              onClick={() => handleUpload().catch(() => undefined)}
              disabled={uploading}
              className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50"
            >
              {uploading ? 'Uploading…' : 'Upload file'}
            </button>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow border p-6 lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-medium text-gray-900">Recent uploads</h2>
            <span className="text-xs text-gray-500">
              Showing {uploads.length} item{uploads.length === 1 ? '' : 's'}
            </span>
          </div>

          {loadingUploads ? (
            <div className="text-sm text-gray-500">Loading uploads…</div>
          ) : uploads.length === 0 ? (
            <div className="text-sm text-gray-500">No manual ingestion uploads recorded yet.</div>
          ) : (
            <div className="space-y-3">
              {uploads.map((upload) => (
                <div key={upload.id} className="border rounded-md p-4">
                  <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-2">
                    <div>
                      <div className="text-sm font-medium text-gray-900">{upload.originalFilename}</div>
                      <div className="text-xs text-gray-500">
                        {upload.sourceSystem} • {upload.dataset || 'unknown dataset'} • Status: <span className="font-semibold">{upload.status}</span>
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        Created {formatDateTime(upload.createdAt)}
                        {upload.externalLocation ? ` • External: ${upload.externalLocation}` : ''}
                      </div>
                      {upload.notes && (
                        <div className="text-xs text-gray-600 mt-1">Notes: {upload.notes}</div>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        className="text-xs px-3 py-1 border rounded hover:bg-gray-50"
                        onClick={() => startHandoff(upload)}
                      >
                        Update handoff
                      </button>
                      <button
                        type="button"
                        className="text-xs px-3 py-1 border border-red-200 text-red-600 rounded hover:bg-red-50"
                        onClick={() => deleteUpload(upload.id)}
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {editingUpload && (
        <div className="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-lg space-y-4">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-lg font-medium text-gray-900">Update handoff</h3>
                <p className="text-sm text-gray-600">{editingUpload.originalFilename}</p>
              </div>
              <button type="button" className="text-gray-500 hover:text-gray-700" onClick={cancelHandoff}>
                Close
              </button>
            </div>

            <div className="space-y-3">
              <div>
                <label className="block text-sm text-gray-700 mb-1" htmlFor="handoffStatus">Status</label>
                <select
                  id="handoffStatus"
                  value={handoffStatus}
                  onChange={(event) => setHandoffStatus(event.target.value as ManualIngestionStatus)}
                  className="w-full border rounded-md px-3 py-2"
                >
                  {statusOptions.map((status) => (
                    <option key={status} value={status}>{status}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm text-gray-700 mb-1" htmlFor="handoffLocation">External location</label>
                <input
                  id="handoffLocation"
                  type="text"
                  value={handoffLocation}
                  onChange={(event) => setHandoffLocation(event.target.value)}
                  className="w-full border rounded-md px-3 py-2"
                  placeholder="Path or URL where the warehouse stored the file"
                />
              </div>

              <div>
                <label className="block text-sm text-gray-700 mb-1" htmlFor="handoffNotes">Notes</label>
                <textarea
                  id="handoffNotes"
                  value={handoffNotes}
                  onChange={(event) => setHandoffNotes(event.target.value)}
                  className="w-full border rounded-md px-3 py-2 min-h-[80px]"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button type="button" className="px-4 py-2 border rounded-md hover:bg-gray-50" onClick={cancelHandoff}>
                Cancel
              </button>
              <button
                type="button"
                className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50"
                disabled={handoffSaving}
                onClick={() => submitHandoff().catch(() => undefined)}
              >
                {handoffSaving ? 'Saving…' : 'Save changes'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ManualIngestionPage;
