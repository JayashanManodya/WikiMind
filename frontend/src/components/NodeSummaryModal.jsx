import React, { useState, useEffect } from 'react';
import { X, BookOpen, ArrowRight, Share2, Loader2 } from 'lucide-react';
import { getWikiPage } from '../api/client';

export default function NodeSummaryModal({ entityName, entityType, onClose, onViewDetailed }) {
  const [loading, setLoading] = useState(true);
  const [contentData, setContentData] = useState(null);

  useEffect(() => {
    if (!entityName) return;

    const fetchDetails = async () => {
      setLoading(true);
      try {
        const res = await getWikiPage(entityName);
        setContentData(res);
      } catch (err) {
        console.error("Failed to fetch node summary details:", err);
        setContentData(null);
      } finally {
        setLoading(false);
      }
    };

    fetchDetails();
  }, [entityName]);

  if (!entityName) return null;

  // Extract overview section from markdown content
  const extractOverview = (rawContent) => {
    if (!rawContent) return "No summary overview available.";
    const parts = rawContent.split("## Overview");
    if (parts.length > 1) {
      const overviewPart = parts[1].split("##")[0].strip ? parts[1].split("##")[0].trim() : parts[1].split("##")[0];
      return overviewPart.substring(0, 350) + (overviewPart.length > 350 ? "..." : "");
    }
    return rawContent.substring(0, 300) + "...";
  };

  return (
    <div 
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(9, 9, 11, 0.45)',
        backdropFilter: 'blur(4px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 10000,
        padding: '20px'
      }}
      onClick={onClose}
    >
      <div 
        className="clean-card"
        style={{
          width: '100%',
          maxWidth: '520px',
          backgroundColor: '#FFFFFF',
          padding: '24px',
          borderRadius: 'var(--radius-lg)',
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
          display: 'flex',
          flexDirection: 'column',
          gap: '16px',
          animation: 'fadeIn 0.2s ease-out'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
              <h2 style={{ fontSize: '20px', fontWeight: '700', color: '#09090B' }}>{entityName}</h2>
              <span className="badge-clean" style={{ fontSize: '10px' }}>{entityType || 'CONCEPT'}</span>
            </div>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Knowledge Base Node</p>
          </div>

          <button 
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              padding: '6px',
              borderRadius: '6px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--text-muted)'
            }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Content Body */}
        {loading ? (
          <div style={{ padding: '30px', textAlign: 'center' }}>
            <Loader2 className="spin" size={24} color="#09090B" style={{ animation: 'spin 1s linear infinite' }} />
            <p style={{ marginTop: '8px', fontSize: '12.5px', color: 'var(--text-muted)' }}>Loading entity summary...</p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            {/* Overview Box */}
            <div style={{ backgroundColor: '#F8FAFC', padding: '14px', borderRadius: '8px', border: '1px solid #E2E8F0' }}>
              <h4 style={{ fontSize: '12px', fontWeight: '600', color: '#475569', marginBottom: '6px', textTransform: 'uppercase' }}>
                Summary Overview
              </h4>
              <p style={{ fontSize: '13px', color: '#1E293B', lineHeight: '1.55' }}>
                {extractOverview(contentData?.content)}
              </p>
            </div>
          </div>
        )}

        {/* Footer Actions */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '8px', paddingTop: '14px', borderTop: '1px solid var(--border-color)' }}>
          <button 
            className="btn btn-outline" 
            onClick={onClose}
            style={{ padding: '8px 16px', fontSize: '13px' }}
          >
            Close
          </button>

          <button 
            className="btn btn-black" 
            onClick={() => {
              onViewDetailed(entityName);
              onClose();
            }}
            style={{ padding: '8px 18px', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <BookOpen size={15} />
            <span>View Detailed Article</span>
            <ArrowRight size={14} />
          </button>
        </div>

      </div>
    </div>
  );
}
