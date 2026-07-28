import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  Layers, 
  BookOpen, 
  Database, 
  Sparkles,
  ArrowRight,
  Sun,
  Shield,
  AlertTriangle
} from 'lucide-react';
import { getDatabaseStats, getDocuments, getWikiIndex } from '../api/client';

export default function DashboardPage({ setActiveTab, setSelectedWikiEntity }) {
  const [stats, setStats] = useState({ documents: 0, entities: 0, relationships: 0, wikiPages: 0 });
  const [recentWikiPages, setRecentWikiPages] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [dbStats, docsRes, wikiRes] = await Promise.all([
          getDatabaseStats().catch(() => ({ total_documents: 0, total_entities: 0, total_relationships: 0 })),
          getDocuments().catch(() => ({ total_documents: 0 })),
          getWikiIndex().catch(() => ({ total_pages: 0, pages: [] }))
        ]);

        setStats({
          documents: docsRes.total_documents || dbStats.total_documents || 0,
          entities: dbStats.total_entities || 0,
          relationships: dbStats.total_relationships || 0,
          wikiPages: wikiRes.total_pages || 0
        });

        if (wikiRes.pages) {
          setRecentWikiPages(wikiRes.pages.slice(0, 6));
        }
      } catch (err) {
        console.error("Dashboard fetch error:", err);
      }
    };

    fetchData();
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      
      {/* Top Header */}
      <div style={{ textAlign: 'center', margin: '20px 0 10px 0' }}>
        <h1 style={{ fontSize: '32px', fontWeight: '700', color: '#09090B', marginBottom: '4px' }}>
          WikiMind
        </h1>
        <p style={{ fontSize: '14px', color: 'var(--text-muted)' }}>
          Version 1.0 • Grounded AI Knowledge System
        </p>
      </div>

      {/* Metrics Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
        <div className="clean-card" style={{ padding: '20px' }}>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '4px' }}>Ingested Documents</p>
          <h2 style={{ fontSize: '26px' }}>{stats.documents}</h2>
        </div>

        <div className="clean-card" style={{ padding: '20px' }}>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '4px' }}>Knowledge Entities</p>
          <h2 style={{ fontSize: '26px' }}>{stats.entities}</h2>
        </div>

        <div className="clean-card" style={{ padding: '20px' }}>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '4px' }}>Wiki Topic Pages</p>
          <h2 style={{ fontSize: '26px' }}>{stats.wikiPages}</h2>
        </div>

        <div className="clean-card" style={{ padding: '20px' }}>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '4px' }}>Vector Search Index</p>
          <h2 style={{ fontSize: '16px', color: '#10B981', marginTop: '6px' }}>Active & Ready</h2>
        </div>
      </div>

      {/* 3-Column ChatGPT Style Cards Layout (Examples, Capabilities, Limitations) */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px' }}>
        
        {/* Examples Column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', justifyContent: 'center', marginBottom: '4px' }}>
            <Sun size={18} color="#71717A" />
            <h3 style={{ fontSize: '15px' }}>Examples</h3>
          </div>

          <div 
            className="clean-card" 
            style={{ padding: '16px', cursor: 'pointer', textAlign: 'center' }}
            onClick={() => setActiveTab('chat')}
          >
            <p style={{ fontSize: '13px', color: 'var(--text-main)' }}>
              "What company did Elon Musk founder and what do they produce?" →
            </p>
          </div>

          <div 
            className="clean-card" 
            style={{ padding: '16px', cursor: 'pointer', textAlign: 'center' }}
            onClick={() => setActiveTab('upload')}
          >
            <p style={{ fontSize: '13px', color: 'var(--text-main)' }}>
              "Upload raw PDF document to generate Wikipedia pages" →
            </p>
          </div>

          <div 
            className="clean-card" 
            style={{ padding: '16px', cursor: 'pointer', textAlign: 'center' }}
            onClick={() => setActiveTab('wiki')}
          >
            <p style={{ fontSize: '13px', color: 'var(--text-main)' }}>
              "Browse topic pages with interactive cross-links" →
            </p>
          </div>
        </div>

        {/* Capabilities Column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', justifyContent: 'center', marginBottom: '4px' }}>
            <Shield size={18} color="#71717A" />
            <h3 style={{ fontSize: '15px' }}>Capabilities</h3>
          </div>

          <div className="clean-card" style={{ padding: '16px', textAlign: 'center' }}>
            <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
              Option A background pipeline automatically parses, cleans, and indexes uploaded files.
            </p>
          </div>

          <div className="clean-card" style={{ padding: '16px', textAlign: 'center' }}>
            <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
              Multi-hop retriever expands Hop-1 vector search with Hop-2 graph relationships.
            </p>
          </div>

          <div className="clean-card" style={{ padding: '16px', textAlign: 'center' }}>
            <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
              Provides exact inline citations (`[Tesla.md]`) to original source documents.
            </p>
          </div>
        </div>

        {/* Limitations Column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', justifyContent: 'center', marginBottom: '4px' }}>
            <AlertTriangle size={18} color="#71717A" />
            <h3 style={{ fontSize: '15px' }}>Limitations</h3>
          </div>

          <div className="clean-card" style={{ padding: '16px', textAlign: 'center' }}>
            <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
              Answers strictly using ingested documents to prevent AI hallucinations.
            </p>
          </div>

          <div className="clean-card" style={{ padding: '16px', textAlign: 'center' }}>
            <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
              Refuses cleanly if knowledge is not found in the stored database.
            </p>
          </div>

          <div className="clean-card" style={{ padding: '16px', textAlign: 'center' }}>
            <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
              Supports PDF, DOCX, TXT, MD document formats.
            </p>
          </div>
        </div>

      </div>

      {/* Generated Wiki Pages Grid */}
      <div className="clean-card" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h3>Stored Wiki Topic Pages</h3>
          <button className="btn btn-outline" onClick={() => setActiveTab('wiki')}>
            View All Wiki Pages
          </button>
        </div>

        {recentWikiPages.length === 0 ? (
          <p style={{ color: 'var(--text-muted)', fontSize: '13px' }}>No wiki pages generated yet. Upload a document to generate topic pages!</p>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: '12px' }}>
            {recentWikiPages.map((page, idx) => (
              <div 
                key={idx} 
                className="clean-card" 
                style={{ padding: '14px', cursor: 'pointer' }}
                onClick={() => {
                  if (setSelectedWikiEntity) setSelectedWikiEntity(page.entity_name);
                  setActiveTab('wiki');
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                  <h4 style={{ fontSize: '14px', fontWeight: '600' }}>{page.entity_name}</h4>
                  <span className="badge-clean">{page.entity_type}</span>
                </div>
                <p style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                  {page.link_count} internal links
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

    </div>
  );
}
