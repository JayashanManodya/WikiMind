import React, { useState } from 'react';
import { 
  UploadCloud, 
  CheckCircle2, 
  AlertCircle, 
  Loader2, 
  FileText, 
  Brain,
  Database,
  Zap,
  ArrowRight
} from 'lucide-react';
import { uploadDocument } from '../api/client';

export default function UploadPage({ setActiveTab }) {
  const [file, setFile] = useState(null);
  const [autoProcess, setAutoProcess] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [currentStep, setCurrentStep] = useState(0); // 0: Idle, 1: Parsing, 2: Knowledge, 3: DB & Wiki, 4: Vector DB, 5: Complete
  const [pipelineResult, setPipelineResult] = useState(null);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
      setPipelineResult(null);
      setCurrentStep(0);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
      setError(null);
      setPipelineResult(null);
      setCurrentStep(0);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError("Please select a file to upload.");
      return;
    }

    setIsUploading(true);
    setError(null);
    setPipelineResult(null);
    setCurrentStep(1);

    // Dynamic stage progression timer giving 5 seconds per step for smooth UX feedback
    const stepTimer = setInterval(() => {
      setCurrentStep((prev) => {
        if (prev >= 1 && prev < 4) return prev + 1;
        return prev;
      });
    }, 5000);

    try {
      const res = await uploadDocument(file, autoProcess);
      clearInterval(stepTimer);
      setCurrentStep(5);
      setPipelineResult(res);
    } catch (err) {
      clearInterval(stepTimer);
      setCurrentStep(0);
      const msg = err.response?.data?.detail || "Error uploading document.";
      setError(msg);
    } finally {
      setIsUploading(false);
    }
  };

  const steps = [
    { id: 1, label: 'Parsing Document Layout & Text', icon: FileText, desc: 'LlamaParse layout processing' },
    { id: 2, label: 'Extracting Knowledge & Facts', icon: Brain, desc: 'LLM Multi-entity intelligence extraction' },
    { id: 3, label: 'Generating Wiki & DB Records', icon: Database, desc: 'Saving content_md to SQL Database' },
    { id: 4, label: 'Vector DB Embedding & Indexing', icon: Zap, desc: 'Generating embeddings in Vector DB' },
  ];

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Header */}
      <div>
        <h2 style={{ fontSize: '22px', fontWeight: '700', marginBottom: '4px' }}>Document Ingestion</h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '13.5px' }}>
          Upload PDF, DOCX, TXT, or MD documents to automatically extract knowledge, generate structured Wiki pages, and index vector embeddings for grounded QA.
        </p>
      </div>

      {/* Upload Drag & Drop Area matching Reference Image */}
      <div 
        className="clean-card"
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
        style={{
          padding: '44px 24px',
          textAlign: 'center',
          border: '2px dashed #E4E4E7',
          backgroundColor: '#FFFFFF',
          borderRadius: '12px',
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
          <div style={{ width: '48px', height: '48px', borderRadius: '50%', backgroundColor: '#F4F4F5', margin: '0 auto 12px auto', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <UploadCloud color="#09090B" size={22} />
          </div>
          
          {file ? (
            <div>
              <p style={{ fontSize: '15px', fontWeight: '600', color: '#09090B' }}>{file.name}</p>
              <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
                {(file.size / 1024 / 1024).toFixed(2)} MB • Ready to process
              </p>
            </div>
          ) : (
            <div>
              <p style={{ fontSize: '14.5px', fontWeight: '500', color: '#09090B' }}>
                Drag & drop or <span style={{ color: '#2563EB', fontWeight: '600' }}>choose files</span> to upload.
              </p>
              <p style={{ fontSize: '11.5px', color: '#71717A', marginTop: '6px' }}>
                Support formats: .csv, .json, .pdf, .xlsx, .txt, .md, .docx, .pptx • Max 25MB per file
              </p>
            </div>
          )}
        </label>
      </div>

      {/* Option Pills matching Reference Design */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', flexWrap: 'wrap' }}>
        <button className="btn btn-outline" style={{ fontSize: '12px', padding: '6px 12px', borderRadius: '8px', color: '#09090B' }}>
          <span style={{ color: '#4285F4', fontWeight: '700' }}>G</span> Add Google Drive
        </button>
        <button className="btn btn-outline" style={{ fontSize: '12px', padding: '6px 12px', borderRadius: '8px', color: '#09090B' }}>
          Add existing knowledge
        </button>
        <button className="btn btn-outline" style={{ fontSize: '12px', padding: '6px 12px', borderRadius: '8px', color: '#09090B' }}>
          Import website
        </button>
        <button className="btn btn-outline" style={{ fontSize: '12px', padding: '6px 12px', borderRadius: '8px', color: '#09090B' }}>
          Blank table
        </button>
        <button className="btn btn-outline" style={{ fontSize: '12px', padding: '6px 12px', borderRadius: '8px', color: '#09090B' }}>
          Markdown/Text
        </button>
      </div>

      {/* Dynamic Ingestion Stepper Card */}
      {isUploading && (
        <div className="clean-card" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px', backgroundColor: '#FAFAFA' }}>
          <h3 style={{ fontSize: '15px', fontWeight: '600', color: '#09090B' }}>
            Ingesting Document: <span style={{ fontWeight: '500' }}>{file?.name}</span>
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {steps.map((st) => {
              const Icon = st.icon;
              const isDone = currentStep > st.id || currentStep === 5;
              const isCurrent = currentStep === st.id;

              return (
                <div key={st.id} style={{ display: 'flex', alignItems: 'center', gap: '14px', padding: '10px 14px', borderRadius: '8px', backgroundColor: isCurrent ? '#FFFFFF' : 'transparent', border: isCurrent ? '1px solid #E4E4E7' : '1px solid transparent', transition: 'all 0.3s ease' }}>
                  <div style={{ 
                    width: '32px', 
                    height: '32px', 
                    borderRadius: '50%', 
                    backgroundColor: isDone ? '#10B981' : isCurrent ? '#09090B' : '#E4E4E7',
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'center',
                    color: '#FFFFFF'
                  }}>
                    {isDone ? (
                      <CheckCircle2 size={18} />
                    ) : isCurrent ? (
                      <Loader2 size={16} className="spin" style={{ animation: 'spin 1s linear infinite' }} />
                    ) : (
                      <Icon size={16} color="#71717A" />
                    )}
                  </div>

                  <div style={{ flex: 1 }}>
                    <p style={{ fontSize: '13.5px', fontWeight: isCurrent ? '600' : '500', color: isCurrent ? '#09090B' : isDone ? '#10B981' : '#71717A' }}>
                      {st.label}
                    </p>
                    <p style={{ fontSize: '11.5px', color: '#71717A' }}>{st.desc}</p>
                  </div>

                  {isDone && <span style={{ fontSize: '12px', fontWeight: '600', color: '#10B981' }}>Done</span>}
                  {isCurrent && <span style={{ fontSize: '12px', fontWeight: '600', color: '#09090B' }}>Processing...</span>}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Submit Button */}
      {!isUploading && (
        <button 
          className="btn btn-black" 
          onClick={handleUpload} 
          disabled={!file || isUploading}
          style={{ padding: '12px 24px', fontSize: '14px', justifyContent: 'center' }}
        >
          <UploadCloud size={16} />
          <span>Start Document Ingestion</span>
        </button>
      )}

      {/* Error Card */}
      {error && (
        <div className="clean-card" style={{ padding: '14px', backgroundColor: '#FEF2F2', borderColor: '#FCA5A5', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <AlertCircle color="#DC2626" size={18} />
          <p style={{ fontSize: '13px', color: '#DC2626' }}>{error}</p>
        </div>
      )}

      {/* Success Result Card */}
      {pipelineResult && !isUploading && (
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
