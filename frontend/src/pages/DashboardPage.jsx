import React, { useState, useEffect } from 'react';
import {
  BookOpen,
  Share2,
  ArrowRight,
  Shield,
  UploadCloud,
  MessageSquare,
  Search,
  Sparkles,
  Zap,
  UserCheck,
  CheckCircle2,
  Filter,
  Layers,
  FileText,
  ExternalLink
} from 'lucide-react';
import { getWikiIndex, getWikiGraph } from '../api/client';
import { useAuth } from '../context/AuthContext';

export default function DashboardPage({ setActiveTab, setSelectedWikiEntity }) {
  const { user } = useAuth();
  const [stats, setStats] = useState({ wikiPages: 0, graphNodes: 0, graphEdges: 0 });
  const [allWikiPages, setAllWikiPages] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeCategory, setActiveCategory] = useState('ALL');
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
          setAllWikiPages(wikiRes.pages);
        } else {
          setAllWikiPages([]);
        }
      } catch (err) {
        console.error("Dashboard fetch error:", err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [user]);

  const categories = ['ALL', 'SYSTEM', 'PERSON', 'CONCEPT', 'PRODUCT', 'COMPONENT', 'HARDWARE'];

  const filteredPages = allWikiPages.filter((page) => {
    const matchesSearch = page.entity_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (page.filename && page.filename.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesCategory = activeCategory === 'ALL' || page.entity_type === activeCategory;
    return matchesSearch && matchesCategory;
  });

  const cardGradients = [
    'linear-gradient(135deg, #0EA5E9 0%, #2563EB 100%)',
    'linear-gradient(135deg, #8B5CF6 0%, #6366F1 100%)',
    'linear-gradient(135deg, #10B981 0%, #059669 100%)',
    'linear-gradient(135deg, #F59E0B 0%, #D97706 100%)',
    'linear-gradient(135deg, #EC4899 0%, #DB2777 100%)',
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '36px', width: '100%', maxWidth: '100%' }}>

      {/* Memora Hero Header Section matching Reference Image */}
      <div className="memora-hero-container">

        {/* Launch Pill Badge */}
        <div className="memora-pill-badge" style={{ marginBottom: '20px' }}>
          <Sparkles size={14} color="#2563EB" />
          <span>⚡ Powered by AI & Graph RAG</span>
        </div>

        {/* Big Bold Memora Headline */}
        <h1 style={{
          fontSize: '44px',
          fontWeight: '800',
          letterSpacing: '-1px',
          color: '#09090B',
          lineHeight: '1.15',
          maxWidth: '720px',
          marginBottom: '16px'
        }}>
          Never lose a piece of <span style={{ color: '#2563EB', background: 'linear-gradient(90deg, #2563EB, #0284C7)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>knowledge</span> again.
        </h1>

        {/* Subtitle */}
        <p style={{
          fontSize: '16px',
          color: '#64748B',
          maxWidth: '620px',
          lineHeight: '1.6',
          marginBottom: '28px'
        }}>
          WikiMind helps you save, organize, and rediscover the most important knowledge you extract from documents - beautifully and effortlessly.
        </p>

        {/* CTA Buttons Row matching Reference Image */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flexWrap: 'wrap', justifyContent: 'center', marginBottom: '24px' }}>
          <button
            className="memora-btn-primary"
            onClick={() => setActiveTab('chat')}
          >
            <span>Start Exploring Knowledge</span>
            <ArrowRight size={16} />
          </button>

          <button
            className="memora-btn-secondary"
            onClick={() => setActiveTab('upload')}
          >
            <UploadCloud size={16} color="#09090B" />
            <span>Upload Document</span>
          </button>
        </div>

        {/* Social Proof Strip matching Reference Image */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '13px', color: '#64748B' }}>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            {['#2563eb', '#10b981', '#f59e0b', '#8b5cf6'].map((col, i) => (
              <div
                key={i}
                style={{
                  width: '24px',
                  height: '24px',
                  borderRadius: '50%',
                  backgroundColor: col,
                  border: '2px solid #FFFFFF',
                  marginLeft: i === 0 ? 0 : '-8px',
                  display: 'flex',
                  alignItems: 'center',
                  justify: 'center',
                  fontSize: '10px',
                  color: '#FFF',
                  fontWeight: '700'
                }}
              >
                {String.fromCharCode(65 + i)}
              </div>
            ))}
          </div>
          <span>Join <strong style={{ color: '#0F172A' }}>{stats.wikiPages > 0 ? stats.wikiPages : 24}+ knowledge topics</strong> indexed & ready</span>
        </div>
      </div>

      {/* Metrics Bar */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
        <div className="memora-card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
            <span style={{ fontSize: '12.5px', color: '#64748B', fontWeight: '500' }}>Stored Wiki Pages</span>
            <BookOpen size={18} color="#2563EB" />
          </div>
          <h2 style={{ fontSize: '32px', fontWeight: '800', color: '#0F172A' }}>{stats.wikiPages}</h2>
          <p style={{ fontSize: '11.5px', color: '#10B981', marginTop: '4px', fontWeight: '500' }}>Saved in SQL Database</p>
        </div>

        <div className="memora-card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
            <span style={{ fontSize: '12.5px', color: '#64748B', fontWeight: '500' }}>Graph Topics</span>
            <Share2 size={18} color="#0EA5E9" />
          </div>
          <h2 style={{ fontSize: '32px', fontWeight: '800', color: '#0F172A' }}>{stats.graphNodes}</h2>
          <p style={{ fontSize: '11.5px', color: '#64748B', marginTop: '4px' }}>Structured Entity Nodes</p>
        </div>

        <div className="memora-card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
            <span style={{ fontSize: '12.5px', color: '#64748B', fontWeight: '500' }}>Relationship Triples</span>
            <Share2 size={18} color="#10B981" />
          </div>
          <h2 style={{ fontSize: '32px', fontWeight: '800', color: '#0F172A' }}>{stats.graphEdges}</h2>
          <p style={{ fontSize: '11.5px', color: '#64748B', marginTop: '4px' }}>Traversable Graph Edges</p>
        </div>

        <div className="memora-card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
            <span style={{ fontSize: '12.5px', color: '#64748B', fontWeight: '500' }}>Security Engine</span>
            <Shield size={18} color="#10B981" />
          </div>
          <h2 style={{ fontSize: '18px', fontWeight: '700', color: '#10B981', marginTop: '6px' }}>Pinecone Namespace</h2>
          <p style={{ fontSize: '11.5px', color: '#64748B', marginTop: '4px' }}>User Isolated Storage</p>
        </div>
      </div>

      {/* Memora Dashboard Product Interface (matching bottom interface of Reference Image) */}
      <div style={{ backgroundColor: '#FFFFFF', border: '1px solid #E2E8F0', borderRadius: '20px', padding: '28px', boxShadow: '0 8px 30px rgba(0,0,0,0.04)' }}>

        {/* Top Control Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px', marginBottom: '24px' }}>
          <div>
            <h3 style={{ fontSize: '20px', fontWeight: '700', color: '#0F172A' }}>Knowledge Base Collection</h3>
            <p style={{ fontSize: '13px', color: '#64748B' }}>Showing {filteredPages.length} of {allWikiPages.length} stored knowledge topics</p>
          </div>

          {/* Search Input Bar */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            backgroundColor: '#F8FAFC',
            border: '1px solid #E2E8F0',
            borderRadius: '9999px',
            padding: '8px 18px',
            gap: '10px',
            width: '320px'
          }}>
            <Search size={16} color="#64748B" />
            <input
              type="text"
              placeholder="Search knowledge..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                flex: 1,
                border: 'none',
                outline: 'none',
                backgroundColor: 'transparent',
                fontSize: '13px',
                color: '#0F172A'
              }}
            />
          </div>
        </div>

        {/* Category Filter Pills */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap', marginBottom: '24px' }}>
          <span style={{ fontSize: '12px', fontWeight: '600', color: '#64748B', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Filter size={13} /> Filter:
          </span>
          {categories.map((cat) => {
            const isSel = activeCategory === cat;
            return (
              <button
                key={cat}
                onClick={() => setActiveCategory(cat)}
                style={{
                  backgroundColor: isSel ? '#09090B' : '#F1F5F9',
                  color: isSel ? '#FFFFFF' : '#475569',
                  border: 'none',
                  borderRadius: '9999px',
                  padding: '5px 16px',
                  fontSize: '12.5px',
                  fontWeight: isSel ? '600' : '500',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease'
                }}
              >
                {cat}
              </button>
            );
          })}
        </div>

        {/* Visual Card Grid matching Memora Reference Design */}
        {filteredPages.length === 0 ? (
          <div style={{ padding: '48px', textAlign: 'center', color: '#64748B', fontSize: '14px' }}>
            No matching Wiki topics found. Upload a document to generate topic pages!
          </div>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '20px' }}>
            {filteredPages.map((page, idx) => {
              const bgGrad = cardGradients[idx % cardGradients.length];
              return (
                <div
                  key={idx}
                  className="memora-card"
                  style={{ cursor: 'pointer' }}
                  onClick={() => {
                    if (setSelectedWikiEntity) setSelectedWikiEntity(page.entity_name);
                    setActiveTab('wiki');
                  }}
                >
                  {/* Card Cover Header */}
                  <div style={{
                    height: '110px',
                    background: bgGrad,
                    padding: '14px',
                    display: 'flex',
                    flexDirection: 'column',
                    justify: 'space-between',
                    color: '#FFFFFF'
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{
                        backgroundColor: 'rgba(255,255,255,0.2)',
                        backdropFilter: 'blur(4px)',
                        padding: '2px 10px',
                        borderRadius: '9999px',
                        fontSize: '11px',
                        fontWeight: '600'
                      }}>
                        {page.entity_type || 'CONCEPT'}
                      </span>
                      <ExternalLink size={14} color="#FFFFFF" style={{ opacity: 0.8 }} />
                    </div>

                    <h4 style={{ fontSize: '16px', fontWeight: '700', textShadow: '0 1px 2px rgba(0,0,0,0.2)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {page.entity_name}
                    </h4>
                  </div>

                  {/* Card Body */}
                  <div style={{ padding: '16px' }}>
                    <p style={{ fontSize: '12px', color: '#64748B', marginBottom: '12px', height: '36px', overflow: 'hidden', textOverflow: 'ellipsis', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical' }}>
                      {page.summary || `Exhaustive grounded knowledge article for ${page.entity_name}.`}
                    </p>

                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid #F1F5F9', paddingTop: '10px', fontSize: '11.5px', color: '#94A3B8' }}>
                      <span>📄 {page.filename || 'Ingested Knowledge'}</span>
                      <span style={{ color: '#2563EB', fontWeight: '600' }}>Read Page →</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

    </div>
  );
}
