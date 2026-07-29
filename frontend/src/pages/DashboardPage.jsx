import React, { useState, useEffect } from 'react';
import { 
  BookOpen, 
  Share2, 
  ArrowRight,
  Shield,
  UploadCloud,
  MessageSquare,
  Lock,
  UserCheck
} from 'lucide-react';
import { getWikiIndex, getWikiGraph } from '../api/client';
import { useAuth } from '../context/AuthContext';

export default function DashboardPage({ setActiveTab, setSelectedWikiEntity }) {
  const { user, isAuthenticated, openLoginModal } = useAuth();
  const [stats, setStats] = useState({ wikiPages: 0, graphNodes: 0, graphEdges: 0 });
  const [recentWikiPages, setRecentWikiPages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      try {
        const [wikiRes, graphRes] = await Promise.all([
          getWikiIndex().catch(() => ({ total_pages: 0, pages: [] })),
          getWikiGraph().catch(() => ({ nodes: [], edges: [] }))
        ]);

        setStats({
          wikiPages: wikiRes.total_pages || (wikiRes.pages ? wikiRes.pages.length : 0),
          graphNodes: graphRes.nodes ? graphRes.nodes.length : 0,
          graphEdges: graphRes.edges ? graphRes.edges.length : 0
        });

        if (wikiRes.pages) {
          setRecentWikiPages(wikiRes.pages.slice(0, 6));
        } else {
          setRecentWikiPages([]);
        }
      } catch (err) {
        console.error("Dashboard fetch error:", err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [user]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      
      {/* User Scoped Auth Banner */}
      {!isAuthenticated ? (
        <div style={{
          backgroundColor: '#eff6ff',
          border: '1px solid #bfdbfe',
          borderRadius: '12px',
          padding: '16px 20px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '16px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ padding: '10px', backgroundColor: '#dbeafe', borderRadius: '50%', color: '#2563eb' }}>
              <Lock size={20} />
            </div>
            <div>
              <h4 style={{ margin: 0, fontSize: '14px', fontWeight: '600', color: '#1e3a8a' }}>
                Per-User Private Knowledge Vault
              </h4>
              <p style={{ margin: '2px 0 0 0', fontSize: '12px', color: '#3b82f6' }}>
                Sign in with Google to create your isolated Knowledge Base where every document, Wiki page, and QA context is private to you.
              </p>
            </div>
          </div>
          <button 
            onClick={openLoginModal}
            className="btn"
            style={{ backgroundColor: '#2563eb', color: '#fff', fontSize: '13px', whiteSpace: 'nowrap' }}
          >
            Sign In with Google
          </button>
        </div>
      ) : (
        <div style={{
          backgroundColor: '#f0fdf4',
          border: '1px solid #bbf7d0',
          borderRadius: '12px',
          padding: '12px 18px',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          color: '#166534',
          fontSize: '13px'
        }}>
          <UserCheck size={18} color="#16a34a" />
          <span>Logged in as <strong>{user?.name} ({user?.email})</strong>. Viewing your private knowledge repository.</span>
        </div>
      )}

      {/* Top Header */}
      <div style={{ textAlign: 'center', margin: '10px 0 0 0', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
        <img 
          src="/logo-color.png" 
          alt="WikiMind Logo" 
          style={{ height: '48px', objectFit: 'contain' }} 
        />
        <h1 style={{ fontSize: '32px', fontWeight: '700', color: '#09090B', marginBottom: '2px' }}>
          WikiMind System
        </h1>
        <p style={{ fontSize: '14px', color: 'var(--text-muted)' }}>
          Grounded Knowledge Management & Graph-Aware QA System
        </p>
      </div>

      {/* Metrics Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
        <div className="clean-card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-muted)', marginBottom: '6px' }}>
            <BookOpen size={16} />
            <span style={{ fontSize: '12.5px' }}>Stored Wiki Pages</span>
          </div>
          <h2 style={{ fontSize: '28px', fontWeight: '700' }}>{stats.wikiPages}</h2>
        </div>

        <div className="clean-card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-muted)', marginBottom: '6px' }}>
            <Share2 size={16} />
            <span style={{ fontSize: '12.5px' }}>Knowledge Graph Nodes</span>
          </div>
          <h2 style={{ fontSize: '28px', fontWeight: '700' }}>{stats.graphNodes}</h2>
        </div>

        <div className="clean-card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-muted)', marginBottom: '6px' }}>
            <Share2 size={16} color="#10B981" />
            <span style={{ fontSize: '12.5px' }}>Graph Relationship Edges</span>
          </div>
          <h2 style={{ fontSize: '28px', fontWeight: '700' }}>{stats.graphEdges}</h2>
        </div>

        <div className="clean-card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text-muted)', marginBottom: '6px' }}>
            <Shield size={16} color="#10B981" />
            <span style={{ fontSize: '12.5px' }}>Per-User Isolation</span>
          </div>
          <h2 style={{ fontSize: '15px', color: '#10B981', marginTop: '6px', fontWeight: '600' }}>Active & Isolated</h2>
        </div>
      </div>

      {/* Quick Action Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '20px' }}>
        
        <div 
          className="clean-card" 
          style={{ padding: '20px', cursor: 'pointer', transition: 'transform 0.15s ease' }}
          onClick={() => setActiveTab('upload')}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '10px' }}>
            <div style={{ width: '40px', height: '40px', borderRadius: '10px', backgroundColor: '#F4F4F5', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <UploadCloud size={20} color="#09090B" />
            </div>
            <div>
              <h3 style={{ fontSize: '15px', fontWeight: '600' }}>1. Document Ingestion</h3>
              <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Upload Word & PDF files</p>
            </div>
          </div>
          <p style={{ fontSize: '12.5px', color: 'var(--text-muted)', lineHeight: '1.4' }}>
            Automated 4-step pipeline parses text, cleans noise, generates Wiki `.md` files, and indexes vectors.
          </p>
        </div>

        <div 
          className="clean-card" 
          style={{ padding: '20px', cursor: 'pointer', transition: 'transform 0.15s ease' }}
          onClick={() => setActiveTab('wiki')}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '10px' }}>
            <div style={{ width: '40px', height: '40px', borderRadius: '10px', backgroundColor: '#F4F4F5', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <BookOpen size={20} color="#09090B" />
            </div>
            <div>
              <h3 style={{ fontSize: '15px', fontWeight: '600' }}>2. Wiki & Graph Browser</h3>
              <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Browse Markdown & Triples</p>
            </div>
          </div>
          <p style={{ fontSize: '12.5px', color: 'var(--text-muted)', lineHeight: '1.4' }}>
            Read structured Wiki Markdown pages and explore Knowledge Graph relationship connections.
          </p>
        </div>

        <div 
          className="clean-card" 
          style={{ padding: '20px', cursor: 'pointer', transition: 'transform 0.15s ease' }}
          onClick={() => setActiveTab('chat')}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '10px' }}>
            <div style={{ width: '40px', height: '40px', borderRadius: '10px', backgroundColor: '#F4F4F5', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <MessageSquare size={20} color="#09090B" />
            </div>
            <div>
              <h3 style={{ fontSize: '15px', fontWeight: '600' }}>3. Graph-Aware QA Chat</h3>
              <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Multi-Agent Reasoning</p>
            </div>
          </div>
          <p style={{ fontSize: '12.5px', color: 'var(--text-muted)', lineHeight: '1.4' }}>
            Ask natural language questions. The system retrieves seed Wiki pages and traverses 1-hop relationships.
          </p>
        </div>

      </div>

      {/* Generated Wiki Pages Grid */}
      <div className="clean-card" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <h3>Stored Wiki Topic Pages</h3>
          <button className="btn btn-outline" onClick={() => setActiveTab('wiki')}>
            <span>View All Wiki Pages</span>
            <ArrowRight size={14} />
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
                  <span className="badge-clean">{page.entity_type || 'CONCEPT'}</span>
                </div>
                <p style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                  File: {page.filename}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

    </div>
  );
}
