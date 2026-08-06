import React from 'react';
import { CheckCircle2, AlertCircle, ArrowRight, X, Loader2 } from 'lucide-react';

export default function NotificationToast({ toast, onDismiss, onViewWiki }) {
  if (!toast) return null;

  const isSuccess = toast.status === 'fully_processed' || toast.type === 'success';
  const isError = toast.status === 'failed' || toast.type === 'error';
  const isProcessing = toast.status === 'processing' || toast.type === 'processing';

  return (
    <div
      style={{
        position: 'fixed',
        bottom: '28px',
        right: '28px',
        zIndex: 99999,
        maxWidth: '420px',
        width: 'calc(100vw - 56px)',
        backgroundColor: '#FFFFFF',
        borderRadius: '24px',
        padding: '20px 24px',
        border: isSuccess ? '1px solid #A7F3D0' : isError ? '1px solid #FCA5A5' : '1px solid #93C5FD',
        boxShadow: '0 20px 50px rgba(0, 0, 0, 0.12), 0 4px 16px rgba(0, 0, 0, 0.06)',
        display: 'flex',
        flexDirection: 'column',
        gap: '14px',
        animation: 'slideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
        fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif"
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div
            style={{
              width: '42px',
              height: '42px',
              borderRadius: '50%',
              backgroundColor: isSuccess ? '#ECFDF5' : isError ? '#FEF2F2' : '#EFF6FF',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0
            }}
          >
            {isSuccess && <CheckCircle2 color="#10B981" size={24} />}
            {isError && <AlertCircle color="#EF4444" size={24} />}
            {isProcessing && <Loader2 color="#2563EB" size={22} style={{ animation: 'spin 1s linear infinite' }} />}
          </div>

          <div>
            <h4 style={{ fontSize: '15px', fontWeight: '800', color: '#09090B', margin: 0, letterSpacing: '-0.01em' }}>
              {toast.title || (isSuccess ? "Document Ingestion Complete!" : isProcessing ? "Ingesting Document..." : "Processing Error")}
            </h4>
            <p style={{ fontSize: '13px', color: '#64748B', margin: '4px 0 0 0', lineHeight: '1.4' }}>
              {toast.message}
            </p>
          </div>
        </div>

        <button
          onClick={onDismiss}
          style={{
            background: 'none',
            border: 'none',
            color: '#94A3B8',
            cursor: 'pointer',
            padding: '4px',
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'all 0.2s ease'
          }}
          onMouseEnter={(e) => (e.currentTarget.style.color = '#09090B')}
          onMouseLeave={(e) => (e.currentTarget.style.color = '#94A3B8')}
        >
          <X size={18} />
        </button>
      </div>

      {isSuccess && (
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', paddingTop: '4px' }}>
          <button
            onClick={() => {
              onDismiss();
              if (onViewWiki) onViewWiki();
            }}
            style={{
              backgroundColor: '#09090B',
              color: '#FFFFFF',
              border: 'none',
              padding: '9px 18px',
              borderRadius: '9999px',
              fontSize: '12.5px',
              fontWeight: '700',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              boxShadow: '0 2px 8px rgba(9, 9, 11, 0.15)'
            }}
          >
            <span>View New Wiki Pages</span>
            <ArrowRight size={13} />
          </button>
        </div>
      )}
    </div>
  );
}
