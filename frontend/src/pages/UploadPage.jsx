import React, { useState } from 'react';
import { 
  UploadCloud, 
  CheckCircle2, 
  AlertCircle, 
  Loader2, 
  FileText, 
  ArrowRight
} from 'lucide-react';
import { uploadDocument } from '../api/client';

export default function UploadPage({ setActiveTab }) {
  const [file, setFile] = useState(null);
  const [autoProcess, setAutoProcess] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [pipelineResult, setPipelineResult] = useState(null);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
      setPipelineResult(null);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
      setError(null);
      setPipelineResult(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError("Please select a file to upload.");
      return;
    }

    setIsUploading(true);
    setError(null);

    try {
      const res = await uploadDocument(file, autoProcess);
      setPipelineResult(res);
    } catch (err) {
      const msg = err.response?.data?.detail || "Error uploading document.";
      setError(msg);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Header */}
      <div>
        <h2 style={{ fontSize: '22px', fontWeight: '700', marginBottom: '4px' }}>Document Ingestion</h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '13.5px' }}>
          Upload PDF, DOCX, TXT, or MD documents. Option A automatically executes parsing, knowledge extraction, wiki page generation, and vector indexing.
        </p>
      </div>

      {/* Upload Drag & Drop Area */}
      <div 
        className="clean-card"
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
        style={{
          padding: '48px 24px',
          textAlign: 'center',
          border: '2px dashed var(--border-color)',
          backgroundColor: '#FFFFFF',
          cursor: 'pointer'
        }}
      >
        <input 
          type="file" 
          id="fileInput" 
          onChange={handleFileChange} 
          accept=".pdf,.docx,.txt,.md" 
          style={{ display: 'none' }} 
        />
        
        <label htmlFor="fileInput" style={{ cursor: 'pointer', display: 'block' }}>
          <div style={{ width: '56px', height: '56px', borderRadius: '50%', backgroundColor: '#F4F4F5', margin: '0 auto 16px auto', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <UploadCloud color="#09090B" size={26} />
          </div>
          
          {file ? (
            <div>
              <p style={{ fontSize: '16px', fontWeight: '600', color: '#09090B' }}>{file.name}</p>
              <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
                {(file.size / 1024 / 1024).toFixed(2)} MB • Ready to process
              </p>
            </div>
          ) : (
            <div>
              <p style={{ fontSize: '15px', fontWeight: '500', color: '#09090B' }}>
                Drag and drop your document here, or <span style={{ textDecoration: 'underline' }}>browse</span>
              </p>
              <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '6px' }}>
                Supports PDF, DOCX, TXT, MD up to 25MB
              </p>
            </div>
          )}
        </label>
      </div>

      {/* Option A Toggle Switch */}
      <div className="clean-card" style={{ padding: '16px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h4 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '2px' }}>Option A: Automated Background Ingestion</h4>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            Automatically parses text, extracts DB facts, generates Wiki pages, and updates vector index in 1 step.
          </p>
        </div>

        <label style={{ position: 'relative', display: 'inline-block', width: '44px', height: '24px', cursor: 'pointer' }}>
          <input 
            type="checkbox" 
            checked={autoProcess} 
            onChange={(e) => setAutoProcess(e.target.checked)} 
            style={{ opacity: 0, width: 0, height: 0 }} 
          />
          <span style={{
            position: 'absolute',
            top: 0, left: 0, right: 0, bottom: 0,
            backgroundColor: autoProcess ? '#09090B' : '#E4E4E7',
            borderRadius: '34px',
            transition: '.3s'
          }}>
            <span style={{
              position: 'absolute',
              content: '""',
              height: '18px',
              width: '18px',
              left: autoProcess ? '22px' : '3px',
              bottom: '3px',
              backgroundColor: 'white',
              borderRadius: '50%',
              transition: '.3s'
            }} />
          </span>
        </label>
      </div>

      {/* Submit Button */}
      <button 
        className="btn btn-black" 
        onClick={handleUpload} 
        disabled={!file || isUploading}
        style={{ padding: '12px 24px', fontSize: '14px', justifyContent: 'center' }}
      >
        {isUploading ? (
          <>
            <Loader2 size={16} className="spin" style={{ animation: 'spin 1s linear infinite' }} />
            <span>Ingesting Document...</span>
          </>
        ) : (
          <>
            <UploadCloud size={16} />
            <span>Start Document Ingestion</span>
          </>
        )}
      </button>

      {/* Error Card */}
      {error && (
        <div className="clean-card" style={{ padding: '14px', backgroundColor: '#FEF2F2', borderColor: '#FCA5A5', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <AlertCircle color="#DC2626" size={18} />
          <p style={{ fontSize: '13px', color: '#DC2626' }}>{error}</p>
        </div>
      )}

      {/* Success Result Card */}
      {pipelineResult && (
        <div className="clean-card" style={{ padding: '20px', borderLeft: '4px solid #10B981' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
            <CheckCircle2 color="#10B981" size={20} />
            <div>
              <h3 style={{ fontSize: '16px', fontWeight: '600' }}>Document Successfully Ingested</h3>
              <p style={{ fontSize: '12.5px', color: 'var(--text-muted)' }}>{pipelineResult.message}</p>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '12px', marginTop: '16px' }}>
            <button className="btn btn-black" onClick={() => setActiveTab('wiki')}>
              <span>Browse Wiki Pages</span>
              <ArrowRight size={14} />
            </button>
            <button className="btn btn-outline" onClick={() => setActiveTab('chat')}>
              <span>Ask Questions in Chat</span>
            </button>
          </div>
        </div>
      )}

    </div>
  );
}
