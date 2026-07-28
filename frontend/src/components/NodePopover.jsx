import React, { useState, useEffect } from 'react';
import { X, BookOpen, ArrowRight, Loader2 } from 'lucide-react';
import { getWikiPage } from '../api/client';

export default function NodePopover({ entityName, entityType, position, onClose, onViewDetailed }) {
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
        console.error("Failed to fetch popover details:", err);
        setContentData(null);
      } finally {
        setLoading(false);
      }
    };

    fetchDetails();
  }, [entityName]);

  if (!entityName || !position) return null;

  // Extract brief 2-line overview snippet
  const extractOverview = (rawContent) => {
    if (!rawContent) return "No summary overview available.";
    const parts = rawContent.split("## Overview");
    let text = rawContent;
    if (parts.length > 1) {
      text = parts[1].split("##")[0].trim();
    }
    return text.substring(0, 140) + (text.length > 140 ? "..." : "");
  };

  // Adjust positioning to keep card within screen bounds
  const leftPos = Math.min(window.innerWidth - 300, Math.max(20, position.x + 15));
  const topPos = Math.min(window.innerHeight - 260, Math.max(20, position.y - 40));

  return (
    <div 
      className="clean-card"
      style={{
        position: 'fixed',
        top: `${topPos}px`,
        left: `${leftPos}px`,
        width: '270px',
        backgroundColor: '#FFFFFF',
        padding: '16px',
        borderRadius: '12px',
        boxShadow: '0 12px 28px -4px rgba(0, 0, 0, 0.15), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
        border: '1px solid #E2E8F0',
        display: 'flex',
        flexDirection: 'column',
        gap: '10px',
        zIndex: 10000,
        animation: 'fadeIn 0.15s ease-out'
      }}
      onClick={(e) => e.stopPropagation()}
    >
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div style={{ paddingRight: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap', marginBottom: '2px' }}>
            <h4 style={{ fontSize: '14px', fontWeight: '700', color: '#09090B', lineHeight: '1.2' }}>{entityName}</h4>
            <span className="badge-clean" style={{ fontSize: '9px', padding: '1px 5px' }}>{entityType || 'CONCEPT'}</span>
          </div>
        </div>

        <button 
          onClick={onClose}
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            padding: '2px',
            borderRadius: '4px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'var(--text-muted)'
          }}
        >
          <X size={15} />
        </button>
      </div>

      {/* Brief Overview Snippet */}
      {loading ? (
        <div style={{ padding: '12px 0', textAlign: 'center' }}>
          <Loader2 className="spin" size={16} color="#09090B" style={{ animation: 'spin 1s linear infinite' }} />
          <p style={{ marginTop: '4px', fontSize: '11px', color: 'var(--text-muted)' }}>Loading summary...</p>
        </div>
      ) : (
        <p style={{ fontSize: '12px', color: '#334155', lineHeight: '1.45', backgroundColor: '#F8FAFC', padding: '8px 10px', borderRadius: '6px', border: '1px solid #F1F5F9' }}>
          {extractOverview(contentData?.content)}
        </p>
      )}

      {/* View Detailed Button */}
      <button 
        className="btn btn-black" 
        onClick={() => {
          onViewDetailed(entityName);
          onClose();
        }}
        style={{ width: '100%', padding: '7px 12px', fontSize: '12px', justifyContent: 'center', gap: '6px', marginTop: '2px' }}
      >
        <BookOpen size={13} />
        <span>View Detailed</span>
        <ArrowRight size={12} />
      </button>
    </div>
  );
}
