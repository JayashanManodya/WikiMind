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
import { useAuth } from '../context/AuthContext';
import { useData } from '../context/DataContext';

export default function DashboardPage({ setActiveTab, setSelectedWikiEntity }) {
  const { user } = useAuth();
  const { wikiPages, wikiGraph, loadWikiPages, loadWikiGraph, isLoadingWiki, isLoadingGraph } = useData();

  const [searchQuery, setSearchQuery] = useState('');
  const [activeCategory, setActiveCategory] = useState('ALL');

  useEffect(() => {
    loadWikiPages();
    loadWikiGraph();
  }, [user, loadWikiPages, loadWikiGraph]);

  const allWikiPages = wikiPages || [];
  const stats = {
    wikiPages: allWikiPages.length,
    graphNodes: wikiGraph.nodes ? wikiGraph.nodes.length : 0,
    graphEdges: wikiGraph.edges ? wikiGraph.edges.length : 0
  };
  const isLoading = isLoadingWiki || isLoadingGraph;


  const categories = ['ALL', 'SYSTEM', 'PERSON', 'CONCEPT', 'PRODUCT', 'COMPONENT', 'HARDWARE'];

  const filteredPages = allWikiPages.filter((page) => {
    const matchesSearch = page.entity_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (page.filename && page.filename.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesCategory = activeCategory === 'ALL' || page.entity_type === activeCategory;
    return matchesSearch && matchesCategory;
  });

  const cardGradients = [
    'linear-gradient(135deg, #09090B 0%, #18181B 100%)',
    'linear-gradient(135deg, #18181B 0%, #27272A 100%)',
    'linear-gradient(135deg, #000000 0%, #171717 100%)',
    'linear-gradient(135deg, #27272A 0%, #09090B 100%)',
    'linear-gradient(135deg, #111827 0%, #030712 100%)',
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '36px', width: '100%', maxWidth: '100%' }}>

      {/* Memora Hero Header Section matching Reference Image */}
      <div className="memora-hero-container">

        {/* Brand Logo Header */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '18px' }}>
          <img 
            src="/logo-color.png" 
            alt="WikiMind Logo" 
            style={{ width: '42px', height: '42px', objectFit: 'contain', borderRadius: '10px', boxShadow: '0 4px 12px rgba(37, 99, 235, 0.15)' }} 
          />
          <span style={{ fontSize: '22px', fontWeight: '800', color: '#09090B', letterSpacing: '-0.5px' }}>WikiMind</span>
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

        {/* Social Proof Strip with Real Face Person Avatar Photos */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '13px', color: '#64748B' }}>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            {[
              'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=100&q=80',
              'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=100&q=80',
              'https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=100&q=80',
              'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?auto=format&fit=crop&w=100&q=80'
            ].map((imgUrl, i) => (
              <img
                key={i}
                src={imgUrl}
                alt={`Person ${i + 1}`}
                style={{
                  width: '28px',
                  height: '28px',
                  borderRadius: '50%',
                  objectFit: 'cover',
                  border: '2px solid #FFFFFF',
                  marginLeft: i === 0 ? 0 : '-8px',
                  boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                }}
              />
            ))}
          </div>
          <span>Join <strong style={{ color: '#0F172A' }}>{stats.wikiPages > 0 ? stats.wikiPages : 24}+ knowledge topics</strong> indexed & ready</span>
        </div>
      </div>

      {/* Metrics Bar */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '16px' }}>
        <div className="memora-card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
            <span style={{ fontSize: '12.5px', color: '#64748B', fontWeight: '500' }}>Stored Wiki Pages</span>
            <BookOpen size={18} color="#2563EB" />
          </div>
          <h2 style={{ fontSize: '32px', fontWeight: '800', color: '#0F172A' }}>{stats.wikiPages}</h2>
          <p style={{ fontSize: '11.5px', color: '#10B981', marginTop: '4px', fontWeight: '500' }}>Saved in Cloud Database</p>
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
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '18px' }}>
            {filteredPages.slice(0, 4).map((page, idx) => {
              return (
                <div
                  key={idx}
                  className="memora-card"
                  style={{
                    cursor: 'pointer',
                    backgroundColor: '#FFFFFF',
                    border: '1px solid #E2E8F0',
                    borderRadius: '14px',
                    padding: '20px',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'space-between',
                    gap: '14px',
                    transition: 'all 0.2s ease'
                  }}
                  onClick={() => {
                    if (setSelectedWikiEntity) setSelectedWikiEntity(page.entity_name);
                    setActiveTab('wiki');
                  }}
                >
                  {/* Top Header: Entity Name & Badge */}
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
                      <span style={{
                        backgroundColor: '#F1F5F9',
                        color: '#09090B',
                        padding: '3px 10px',
                        borderRadius: '9999px',
                        fontSize: '11px',
                        fontWeight: '600',
                        border: '1px solid #E2E8F0'
                      }}>
                        {page.entity_type || 'CONCEPT'}
                      </span>
                      <ExternalLink size={14} color="#71717A" />
                    </div>

                    <h4 style={{ fontSize: '16.5px', fontWeight: '700', color: '#09090B', lineHeight: '1.3' }}>
                      {page.entity_name}
                    </h4>
                  </div>

                  {/* Summary Text */}
                  <p style={{
                    fontSize: '13px',
                    color: '#64748B',
                    lineHeight: '1.5',
                    height: '38px',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    display: '-webkit-box',
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: 'vertical',
                    margin: 0
                  }}>
                    {page.summary || `Exhaustive grounded knowledge article for ${page.entity_name}.`}
                  </p>

                  {/* Card Footer Link */}
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    borderTop: '1px solid #F1F5F9',
                    paddingTop: '12px',
                    fontSize: '12px',
                    color: '#94A3B8'
                  }}>
                    <span style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '170px' }}>
                      📄 {page.filename || 'Ingested Document'}
                    </span>
                    <span style={{ color: '#09090B', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      Read Page →
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* View All Topics Button below 1st Row */}
        {allWikiPages.length > 4 && (
          <div style={{ display: 'flex', justifyContent: 'center', marginTop: '24px' }}>
            <button
              className="memora-btn-secondary"
              onClick={() => setActiveTab('wiki')}
              style={{ fontSize: '13px', padding: '8px 20px', gap: '8px' }}
            >
              <span>View All {allWikiPages.length} Knowledge Topics</span>
              <ArrowRight size={15} color="#09090B" />
            </button>
          </div>
        )}
      </div>

    </div>
  );
}
