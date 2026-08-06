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
  ArrowRight,
  Sparkles,
  ShieldCheck
} from 'lucide-react';
import { uploadDocument } from '../api/client';
import { useData } from '../context/DataContext';

export default function UploadPage({ setActiveTab }) {
  const { invalidateAll, addProcessingTask, activeProcessingTasks, toastNotification } = useData();
  const [file, setFile] = useState(null);
  const [autoProcess, setAutoProcess] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [pipelineResult, setPipelineResult] = useState(null);
  const [error, setError] = useState(null);

  const activeTask = activeProcessingTasks.length > 0 ? activeProcessingTasks[0] : null;
  const isProcessingBackground = Boolean(activeTask || isUploading);

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

    try {
      const res = await uploadDocument(file, autoProcess);
      if (res.status === 'processing' && res.file_id) {
        addProcessingTask(res.file_id, file.name);
      } else {
        setPipelineResult(res);
        setCurrentStep(5);
        invalidateAll();
      }
    } catch (err) {
      setCurrentStep(0);
      const msg = err.response?.data?.detail || "Error uploading document.";
      setError(msg);
    } finally {
      setIsUploading(false);
    }
  };

  // Dynamic step progression timer for live progress visualization
  React.useEffect(() => {
    if (!isProcessingBackground) return;

    const timer = setInterval(() => {
      setCurrentStep((prev) => {
        if (prev >= 1 && prev < 4) return prev + 1;
        return prev;
      });
    }, 4000);

    return () => clearInterval(timer);
  }, [isProcessingBackground]);

  // When task completes via polling notification, update stepper and show success card
  React.useEffect(() => {
    if (toastNotification && toastNotification.status === 'fully_processed') {
      setCurrentStep(5);
      setPipelineResult({
        message: toastNotification.message,
        pages_created: toastNotification.pages_created || []
      });
    }
  }, [toastNotification]);

  const steps = [
    { id: 1, label: 'Parsing Document Layout & Text', icon: FileText, desc: 'LlamaParse layout processing' },
    { id: 2, label: 'Extracting Knowledge & Facts', icon: Brain, desc: 'LLM Multi-entity intelligence extraction' },
    { id: 3, label: 'Generating Wiki & Neo4j DB Records', icon: Database, desc: 'Saving content & graph edges to Neo4j DB' },
    { id: 4, label: 'Indexing & Graph Construction', icon: Zap, desc: 'Linking entity references & index catalog' },
  ];


  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', width: '100%', maxWidth: '100%' }}>
      
      {/* Overview Bento Theme Header Card */}
      <div style={{
        backgroundColor: '#FFFFFF',
        borderRadius: '32px',
        padding: '36px 40px',
        border: '1px solid #E2E8F0',
        boxShadow: '0 10px 40px rgba(0,0,0,0.03)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '24px'
      }}>
        <div style={{ maxWidth: '580px' }}>
          <h1 style={{ fontSize: '32px', fontWeight: '800', color: '#09090B', letterSpacing: '-0.8px', margin: '0 0 8px 0' }}>
            Document Ingestion & Pipeline
          </h1>
          <p style={{ fontSize: '14.5px', color: '#64748B', lineHeight: '1.6', margin: 0 }}>
            Upload PDF, DOCX, XLSX, XLS, CSV, TXT, MD, PPTX, or HTML files to automatically extract entities, generate interlinked Wiki pages, and index vector embeddings.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '12px', fontWeight: '700', padding: '6px 14px', borderRadius: '10px', backgroundColor: '#F8FAFC', border: '1px solid #E2E8F0', color: '#DC2626' }}>
            PDF
          </span>
          <span style={{ fontSize: '12px', fontWeight: '700', padding: '6px 14px', borderRadius: '10px', backgroundColor: '#F8FAFC', border: '1px solid #E2E8F0', color: '#2563EB' }}>
            DOCX
          </span>
          <span style={{ fontSize: '12px', fontWeight: '700', padding: '6px 14px', borderRadius: '10px', backgroundColor: '#F8FAFC', border: '1px solid #E2E8F0', color: '#059669' }}>
            EXCEL
          </span>
          <span style={{ fontSize: '12px', fontWeight: '700', padding: '6px 14px', borderRadius: '10px', backgroundColor: '#F8FAFC', border: '1px solid #E2E8F0', color: '#0EA5E9' }}>
            CSV
          </span>
          <span style={{ fontSize: '12px', fontWeight: '700', padding: '6px 14px', borderRadius: '10px', backgroundColor: '#F8FAFC', border: '1px solid #E2E8F0', color: '#64748B' }}>
            TXT
          </span>
          <span style={{ fontSize: '12px', fontWeight: '700', padding: '6px 14px', borderRadius: '10px', backgroundColor: '#F8FAFC', border: '1px solid #E2E8F0', color: '#7C3AED' }}>
            MD
          </span>
          <span style={{ fontSize: '12px', fontWeight: '700', padding: '6px 14px', borderRadius: '10px', backgroundColor: '#F8FAFC', border: '1px solid #E2E8F0', color: '#D97706' }}>
            PPTX
          </span>
        </div>
      </div>

      {/* Main Drag & Drop Bento Card */}
      <div 
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
        style={{
          backgroundColor: '#FFFFFF',
          borderRadius: '28px',
          padding: '48px 32px',
          textAlign: 'center',
          border: '2px dashed #CBD5E1',
          boxShadow: '0 8px 30px rgba(0,0,0,0.02)',
          cursor: 'pointer',
          transition: 'all 0.2s ease'
        }}
      >
        <input 
          type="file" 
          id="fileInput" 
          onChange={handleFileChange} 
          accept=".pdf,.docx,.doc,.txt,.md,.csv,.xlsx,.xls,.pptx,.html" 
          style={{ display: 'none' }} 
        />
        
        <label htmlFor="fileInput" style={{ cursor: 'pointer', display: 'block' }}>
          <div style={{ width: '56px', height: '56px', borderRadius: '50%', backgroundColor: '#EFF6FF', margin: '0 auto 16px auto', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <UploadCloud color="#2563EB" size={26} />
          </div>
          
          {file ? (
            <div>
              <p style={{ fontSize: '17px', fontWeight: '700', color: '#09090B' }}>{file.name}</p>
              <p style={{ fontSize: '13px', color: '#64748B', marginTop: '6px' }}>
                {(file.size / 1024 / 1024).toFixed(2)} MB • Ready to process
              </p>
            </div>
          ) : (
            <div>
              <p style={{ fontSize: '16px', fontWeight: '600', color: '#09090B' }}>
                Drag & drop or <span style={{ color: '#2563EB', fontWeight: '700' }}>browse files</span> to upload
              </p>
              <p style={{ fontSize: '13px', color: '#64748B', marginTop: '8px' }}>
                Supported Formats: PDF, DOCX, XLSX, XLS, CSV, TXT, MD, PPTX, HTML • Max 25MB per file
              </p>
            </div>
          )}
        </label>
      </div>

      {/* Submit Action Button */}
      {!isUploading && (
        <div style={{ display: 'flex', justifyContent: 'center' }}>
          <button 
            onClick={handleUpload} 
            disabled={!file || isUploading}
            style={{
              backgroundColor: '#09090B',
              color: '#FFFFFF',
              border: 'none',
              padding: '14px 32px',
              borderRadius: '9999px',
              fontSize: '15px',
              fontWeight: '700',
              cursor: file ? 'pointer' : 'not-allowed',
              opacity: file ? 1 : 0.6,
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              boxShadow: '0 4px 14px rgba(9, 9, 11, 0.2)',
              transition: 'all 0.2s ease'
            }}
          >
            <UploadCloud size={18} />
            <span>Start Document Ingestion Pipeline</span>
          </button>
        </div>
      )}

      {/* Dynamic Ingestion Stepper Card */}
      {isProcessingBackground && (
        <div style={{ backgroundColor: '#FFFFFF', borderRadius: '28px', padding: '32px', border: '1px solid #E2E8F0', boxShadow: '0 8px 30px rgba(0,0,0,0.03)' }}>
          <h3 style={{ fontSize: '17px', fontWeight: '700', color: '#09090B', marginBottom: '20px' }}>
            Ingesting Document in Background: <span style={{ color: '#2563EB' }}>{file?.name || activeTask?.filename}</span>
          </h3>


          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {steps.map((st) => {
              const Icon = st.icon;
              const isDone = currentStep > st.id || currentStep === 5;
              const isCurrent = currentStep === st.id;

              return (
                <div key={st.id} style={{ display: 'flex', alignItems: 'center', gap: '16px', padding: '14px 18px', borderRadius: '16px', backgroundColor: isCurrent ? '#F8FAFC' : 'transparent', border: isCurrent ? '1px solid #E2E8F0' : '1px solid transparent', transition: 'all 0.2s ease' }}>
                  <div style={{ 
                    width: '36px', 
                    height: '36px', 
                    borderRadius: '50%', 
                    backgroundColor: isDone ? '#10B981' : isCurrent ? '#2563EB' : '#F1F5F9',
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'center',
                    color: '#FFFFFF'
                  }}>
                    {isDone ? (
                      <CheckCircle2 size={20} />
                    ) : isCurrent ? (
                      <Loader2 size={18} style={{ animation: 'spin 1s linear infinite' }} />
                    ) : (
                      <Icon size={18} color="#94A3B8" />
                    )}
                  </div>

                  <div style={{ flex: 1 }}>
                    <p style={{ fontSize: '14px', fontWeight: isCurrent ? '700' : '600', color: isCurrent ? '#09090B' : isDone ? '#10B981' : '#64748B', margin: 0 }}>
                      {st.label}
                    </p>
                    <p style={{ fontSize: '12px', color: '#64748B', margin: '2px 0 0 0' }}>{st.desc}</p>
                  </div>

                  {isDone && <span style={{ fontSize: '13px', fontWeight: '700', color: '#10B981' }}>Done</span>}
                  {isCurrent && <span style={{ fontSize: '13px', fontWeight: '700', color: '#2563EB' }}>Processing...</span>}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Error Card */}
      {error && (
        <div style={{ backgroundColor: '#FEF2F2', borderRadius: '20px', padding: '18px 24px', border: '1px solid #FCA5A5', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <AlertCircle color="#DC2626" size={20} />
          <p style={{ fontSize: '14px', color: '#DC2626', margin: 0, fontWeight: '500' }}>{error}</p>
        </div>
      )}

      {/* Success Result Card */}
      {pipelineResult && !isUploading && (
        <div style={{ backgroundColor: '#FFFFFF', borderRadius: '28px', padding: '32px', border: '1px solid #A7F3D0', borderLeft: '6px solid #10B981', boxShadow: '0 8px 30px rgba(16, 185, 129, 0.08)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px', marginBottom: '16px' }}>
            <CheckCircle2 color="#10B981" size={24} />
            <div>
              <h3 style={{ fontSize: '18px', fontWeight: '800', color: '#064E3B', margin: 0 }}>Document Successfully Ingested</h3>
              <p style={{ fontSize: '13.5px', color: '#047857', margin: '4px 0 0 0' }}>{pipelineResult.message}</p>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '12px', marginTop: '20px', flexWrap: 'wrap' }}>
            <button 
              onClick={() => setActiveTab('wiki')}
              style={{ backgroundColor: '#09090B', color: '#FFFFFF', border: 'none', padding: '12px 24px', borderRadius: '9999px', fontSize: '13.5px', fontWeight: '700', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px' }}
            >
              <span>Browse Knowledge Graph</span>
              <ArrowRight size={14} />
            </button>
            <button 
              onClick={() => setActiveTab('chat')}
              style={{ backgroundColor: '#FFFFFF', color: '#09090B', border: '1px solid #E2E8F0', padding: '12px 24px', borderRadius: '9999px', fontSize: '13.5px', fontWeight: '700', cursor: 'pointer' }}
            >
              <span>Ask Questions in Chat</span>
            </button>
          </div>
        </div>
      )}

    </div>
  );
}
