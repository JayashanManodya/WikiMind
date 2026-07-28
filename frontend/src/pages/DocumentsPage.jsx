import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  RefreshCw, 
  CheckCircle2, 
  Loader2
} from 'lucide-react';
import { getDocuments, processFullPipeline } from '../api/client';

export default function DocumentsPage() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [processingId, setProcessingId] = useState(null);

  const fetchDocs = async () => {
    setLoading(true);
    try {
      const res = await getDocuments();
      if (res.documents) {
        setDocuments(res.documents);
      }
    } catch (err) {
      console.error("Fetch documents error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocs();
  }, []);

  const handleReprocess = async (fileId) => {
    setProcessingId(fileId);
    try {
      await processFullPipeline(fileId);
      await fetchDocs();
    } catch (err) {
      alert("Error re-processing pipeline: " + (err.response?.data?.detail || err.message));
    } finally {
      setProcessingId(null);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontSize: '20px', fontWeight: '700' }}>Document Storage Manager</h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '13px' }}>
            Stored raw files and manual pipeline triggers.
          </p>
        </div>

        <button className="btn btn-outline" onClick={fetchDocs} disabled={loading}>
          <RefreshCw size={14} className={loading ? "spin" : ""} />
          <span>Refresh List</span>
        </button>
      </div>

      <div className="clean-card" style={{ overflow: 'hidden' }}>
        {loading ? (
          <div style={{ padding: '60px', textAlign: 'center' }}>
            <Loader2 className="spin" size={24} color="#09090B" style={{ animation: 'spin 1s linear infinite' }} />
            <p style={{ marginTop: '10px', fontSize: '13px', color: 'var(--text-muted)' }}>Loading stored documents...</p>
          </div>
        ) : documents.length === 0 ? (
          <div style={{ padding: '60px', textAlign: 'center', color: 'var(--text-muted)' }}>
            <FileText size={40} color="var(--border-color)" style={{ marginBottom: '10px' }} />
            <p style={{ fontSize: '13px' }}>No documents stored yet.</p>
          </div>
        ) : (
          <table className="clean-table">
            <thead>
              <tr>
                <th>Document</th>
                <th>File ID</th>
                <th>Size</th>
                <th>Status</th>
                <th>Upload Date</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {documents.map((doc, idx) => (
                <tr key={idx}>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <FileText size={16} color="#09090B" />
                      <span style={{ fontWeight: '500' }}>{doc.original_filename}</span>
                    </div>
                  </td>

                  <td>
                    <span style={{ fontFamily: 'monospace', fontSize: '12px', color: 'var(--text-muted)' }}>
                      {doc.file_id?.slice(0, 16)}...
                    </span>
                  </td>

                  <td>
                    <span style={{ fontSize: '12.5px', color: 'var(--text-muted)' }}>
                      {(doc.file_size_bytes / 1024).toFixed(1)} KB
                    </span>
                  </td>

                  <td>
                    <span className="badge-clean">
                      <CheckCircle2 size={11} color="#10B981" />
                      {doc.status}
                    </span>
                  </td>

                  <td>
                    <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                      {new Date(doc.upload_timestamp).toLocaleDateString()}
                    </span>
                  </td>

                  <td>
                    <button 
                      className="btn btn-outline" 
                      onClick={() => handleReprocess(doc.file_id)}
                      disabled={processingId === doc.file_id}
                      style={{ padding: '4px 10px', fontSize: '11.5px' }}
                    >
                      {processingId === doc.file_id ? (
                        <Loader2 className="spin" size={12} style={{ animation: 'spin 1s linear infinite' }} />
                      ) : (
                        <RefreshCw size={12} />
                      )}
                      <span>Re-process</span>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

    </div>
  );
}
