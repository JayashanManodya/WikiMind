import React, { useState, useEffect } from 'react';
import {
  BookOpen,
  Share2,
  ArrowUpRight,
  ArrowRight,
  UploadCloud,
  MessageSquare,
  Search,
  Sparkles,
  Zap,
  CheckCircle2,
  FileText,
  ShieldCheck,
  HelpCircle,
  Network
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useData } from '../context/DataContext';
import HeroNodeGraph from '../components/HeroNodeGraph';
import Footer from '../components/Footer';

export default function DashboardPage({ setActiveTab, setSelectedWikiEntity }) {
  const { user } = useAuth();
  const { wikiPages, wikiGraph, loadWikiPages, loadWikiGraph, isLoadingWiki, isLoadingGraph } = useData();

  const [searchQuery, setSearchQuery] = useState('');
  const [activeCategory, setActiveCategory] = useState('ALL');

  useEffect(() => {
    loadWikiPages();
    loadWikiGraph();
  }, []);

  const allWikiPages = wikiPages || [];
  const stats = {
    wikiPages: allWikiPages.length,
    graphNodes: wikiGraph?.nodes?.length || 0,
    graphEdges: wikiGraph?.edges?.length || 0
  };

  const categories = ['ALL', 'CONCEPT', 'PERSON', 'ORGANIZATION', 'TECHNOLOGY', 'HARDWARE', 'COMPONENT'];

  const filteredPages = allWikiPages.filter((page) => {
    const matchesSearch = (page.entity_name || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      (page.summary || '').toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCat = activeCategory === 'ALL' || (page.entity_type || 'CONCEPT').toUpperCase() === activeCategory;
    return matchesSearch && matchesCat;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', width: '100%', maxWidth: '100%' }}>

      {/* UNIFIED MERGED WHITE HERO CARD (Headline + Interactive Node Graph in ONE Crisp White Bento Box) */}
      <div style={{
        backgroundColor: '#FFFFFF',
        borderRadius: '32px',
        padding: '44px 48px',
        border: '1px solid #E2E8F0',
        boxShadow: '0 10px 40px rgba(0,0,0,0.03)',
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))',
        gap: '40px',
        alignItems: 'center',
        position: 'relative',
        overflow: 'hidden'
      }}>

        {/* Left Column: Headline, Controls & Stats */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '28px', zIndex: 2 }}>

          {/* Top Brand Logo */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <img
              src="/logo-color.png"
              alt="WikiMind Logo"
              style={{ width: '36px', height: '36px', objectFit: 'contain', borderRadius: '8px' }}
            />
            <span style={{ fontSize: '20px', fontWeight: '800', color: '#09090B', letterSpacing: '-0.5px' }}>WikiMind</span>
          </div>

          {/* Big Bold Headline */}
          <h1 style={{
            fontSize: '48px',
            fontWeight: '800',
            letterSpacing: '-1.5px',
            color: '#09090B',
            lineHeight: '1.1',
            margin: 0
          }}>
            Control your <span style={{ color: '#2563EB' }}>knowledge</span> base easily
          </h1>

          {/* Subtitle */}
          <p style={{
            fontSize: '15px',
            color: '#64748B',
            lineHeight: '1.6',
            margin: 0,
            maxWidth: '480px'
          }}>
            Streamline your document intelligence with our intuitive Graph RAG platform. Automatically extract entities, interlink wiki topics, and ask grounded questions.
          </p>

          {/* CTA Buttons (Pill + Circular Arrow Badge + Guide Button) */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
            <button
              onClick={() => setActiveTab('chat')}
              style={{
                backgroundColor: '#D9F99D', // Lime yellow pill button matching reference image
                color: '#09090B',
                border: 'none',
                padding: '14px 24px',
                borderRadius: '9999px',
                fontSize: '15px',
                fontWeight: '700',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                boxShadow: '0 4px 14px rgba(217, 249, 157, 0.5)',
                transition: 'transform 0.15s ease'
              }}
            >
              <span>Start Exploring</span>
              <div style={{
                width: '32px',
                height: '32px',
                borderRadius: '50%',
                backgroundColor: '#09090B',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
                padding: 0,
                margin: 0
              }}>
                <ArrowUpRight size={18} color="#FFFFFF" style={{ display: 'block' }} />
              </div>
            </button>

            <button
              onClick={() => setActiveTab('upload')}
              style={{
                backgroundColor: '#F4F4F5',
                color: '#09090B',
                border: '1px solid #E4E4E7',
                padding: '14px 24px',
                borderRadius: '9999px',
                fontSize: '14px',
                fontWeight: '600',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}
            >
              <UploadCloud size={16} color="#09090B" />
              <span>Upload File</span>
            </button>

            <button
              onClick={() => setActiveTab('guide')}
              style={{
                backgroundColor: '#EFF6FF',
                color: '#2563EB',
                border: '1px solid #BFDBFE',
                padding: '14px 24px',
                borderRadius: '9999px',
                fontSize: '14px',
                fontWeight: '600',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}
            >
              <HelpCircle size={16} color="#2563EB" />
              <span>Platform Guide</span>
            </button>
          </div>

          {/* Bottom Social Proof & Metrics Strip */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justify: 'space-between',
            paddingTop: '20px',
            borderTop: '1px solid #F1F5F9',
            flexWrap: 'wrap',
            gap: '16px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ display: 'flex', alignItems: 'center' }}>
                {[
                  { icon: FileText, bg: '#EF4444', title: 'Document Ingestion' },
                  { icon: Network, bg: '#10B981', title: 'Knowledge Graph' },
                  { icon: Sparkles, bg: '#2563EB', title: 'Citation AI QA' }
                ].map((badge, i) => {
                  const Icon = badge.icon;
                  return (
                    <div
                      key={i}
                      title={badge.title}
                      style={{
                        width: '34px',
                        height: '34px',
                        borderRadius: '50%',
                        backgroundColor: badge.bg,
                        display: 'inline-flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        border: '2px solid #FFFFFF',
                        marginLeft: i === 0 ? 0 : '-10px',
                        boxShadow: '0 4px 10px rgba(0,0,0,0.15)',
                        zIndex: 3 - i
                      }}
                    >
                      <Icon size={16} color="#FFFFFF" />
                    </div>
                  );
                })}
              </div>
              <div>
                <span style={{ fontSize: '18px', fontWeight: '800', color: '#09090B', display: 'block', lineHeight: '1.1' }}>
                  {stats.wikiPages > 0 ? stats.wikiPages : 24}+ Knowledge Topics
                </span>
                <span style={{ fontSize: '12px', color: '#64748B' }}>100% Grounded & Citation Backed</span>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <div>
                <span style={{ fontSize: '18px', fontWeight: '800', color: '#09090B', display: 'block', lineHeight: '1.1' }}>{stats.graphNodes}</span>
                <span style={{ fontSize: '11.5px', color: '#64748B' }}>Nodes</span>
              </div>
              <div style={{ width: '1px', height: '24px', backgroundColor: '#E2E8F0' }} />
              <div>
                <span style={{ fontSize: '18px', fontWeight: '800', color: '#09090B', display: 'block', lineHeight: '1.1' }}>{stats.graphEdges}</span>
                <span style={{ fontSize: '11.5px', color: '#64748B' }}>Edges</span>
              </div>
            </div>
          </div>

        </div>

        {/* Right Column: Floating Interactive Physics Node Graph Canvas (No Inner Card Box) */}
        <div style={{
          position: 'relative',
          width: '100%',
          height: '380px',
          display: 'flex',
          alignItems: 'center',
          justify: 'center',
          zIndex: 2
        }}>
          <HeroNodeGraph isLight={false} />
        </div>

      </div>



      {/* BOTTOM BENTO ROW: 3 Distinct Bento Cards (Ref Image Layout) */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
        gap: '24px'
      }}>

        {/* BOTTOM CARD 1: AI Ask Feature Highlight */}
        <div style={{
          backgroundColor: '#FFFFFF',
          borderRadius: '28px',
          padding: '28px',
          border: '1px solid #E2E8F0',
          boxShadow: '0 8px 30px rgba(0,0,0,0.02)',
          display: 'flex',
          flexDirection: 'column',
          justify: 'space-between',
          position: 'relative'
        }}>
          {/* Floating badge pill 1 */}
          <div style={{
            position: 'absolute',
            top: '20px',
            left: '20px',
            backgroundColor: '#059669',
            color: '#FFFFFF',
            fontSize: '11px',
            fontWeight: '700',
            padding: '4px 12px',
            borderRadius: '9999px',
            transform: 'rotate(-6deg)',
            boxShadow: '0 4px 10px rgba(5, 150, 105, 0.3)'
          }}>
            Zero Hallucination
          </div>

          {/* Floating badge pill 2 */}
          <div style={{
            position: 'absolute',
            top: '20px',
            right: '20px',
            backgroundColor: '#2563EB',
            color: '#FFFFFF',
            fontSize: '11px',
            fontWeight: '700',
            padding: '4px 12px',
            borderRadius: '9999px',
            transform: 'rotate(8deg)',
            boxShadow: '0 4px 10px rgba(37, 99, 235, 0.3)'
          }}>
            Citation Grounded
          </div>

          <div style={{ marginTop: '48px' }}>
            <h3 style={{ fontSize: '20px', fontWeight: '800', color: '#09090B', marginBottom: '8px', lineHeight: '1.25' }}>
              Ask AI Anything with Zero Hallucination
            </h3>
            <p style={{ fontSize: '13px', color: '#64748B', lineHeight: '1.5', margin: 0 }}>
              Grounded AI assistant answering questions with instant click-through citations to your knowledge base.
            </p>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: '#10B981', marginTop: '12px', fontWeight: '600' }}>
              <ShieldCheck size={16} color="#10B981" />
              <span>Grounded QA Engine Active</span>
            </div>
          </div>

          <button
            onClick={() => setActiveTab('chat')}
            style={{
              marginTop: '20px',
              alignSelf: 'flex-start',
              backgroundColor: '#09090B',
              color: '#FFFFFF',
              border: 'none',
              padding: '10px 20px',
              borderRadius: '9999px',
              fontSize: '13px',
              fontWeight: '700',
              cursor: 'pointer',
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              boxShadow: '0 4px 12px rgba(9, 9, 11, 0.15)'
            }}
          >
            <span>Ask AI Assistant</span>
            <MessageSquare size={14} />
          </button>
        </div>

        {/* BOTTOM CARD 2: Connect Easily / Knowledge Base Quick List (Explore Topics) */}
        <div style={{
          backgroundColor: '#FFFFFF',
          borderRadius: '28px',
          padding: '28px',
          border: '1px solid #E2E8F0',
          boxShadow: '0 8px 30px rgba(0,0,0,0.02)',
          display: 'flex',
          flexDirection: 'column',
          justify: 'space-between'
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '18px' }}>
              <h3 style={{ fontSize: '18px', fontWeight: '700', color: '#09090B' }}>Explore Knowledge Pages</h3>
              <button
                onClick={() => setActiveTab('wiki')}
                style={{ background: 'none', border: 'none', fontSize: '13px', color: '#64748B', cursor: 'pointer', fontWeight: '500' }}
              >
                See all
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {filteredPages.slice(0, 2).map((pg, idx) => (
                <div
                  key={idx}
                  onClick={() => {
                    if (setSelectedWikiEntity) setSelectedWikiEntity(pg.entity_name);
                    setActiveTab('wiki');
                  }}
                  style={{
                    backgroundColor: '#F8FAFC',
                    borderRadius: '16px',
                    padding: '12px 16px',
                    display: 'flex',
                    alignItems: 'center',
                    justify: 'space-between',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div style={{ width: '36px', height: '36px', borderRadius: '50%', backgroundColor: '#EFF6FF', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <BookOpen size={16} color="#2563EB" />
                    </div>
                    <div>
                      <h4 style={{ fontSize: '13.5px', fontWeight: '700', color: '#09090B', margin: 0 }}>{pg.entity_name}</h4>
                      <span style={{ fontSize: '11px', color: '#64748B' }}>{pg.entity_type || 'CONCEPT'}</span>
                    </div>
                  </div>
                  <div style={{ width: '28px', height: '28px', borderRadius: '50%', backgroundColor: '#FFFFFF', border: '1px solid #E2E8F0', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <ArrowRight size={12} color="#09090B" />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* BOTTOM CARD 3: Document Uploading & Ingestion Feature */}
        <div style={{
          backgroundColor: '#ECFDF5',
          borderRadius: '28px',
          padding: '28px',
          border: '1px solid #A7F3D0',
          boxShadow: '0 8px 30px rgba(16, 185, 129, 0.05)',
          display: 'flex',
          flexDirection: 'column',
          justify: 'space-between',
          position: 'relative'
        }}>
          <div>
            <span style={{ fontSize: '12px', fontWeight: '700', color: '#047857', backgroundColor: '#D1FAE5', padding: '4px 10px', borderRadius: '9999px' }}>
              Multi-Format Ingestion
            </span>
            <h3 style={{ fontSize: '22px', fontWeight: '800', color: '#064E3B', marginTop: '14px', marginBottom: '8px', lineHeight: '1.2' }}>
              Upload Documents & Build Knowledge!
            </h3>
            <p style={{ fontSize: '13px', color: '#047857', lineHeight: '1.5' }}>
              Upload PDFs, Word DOCX, Excel spreadsheets, and text files for automatic entity extraction and interlinked wiki creation.
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '20px' }}>
            <button
              onClick={() => setActiveTab('upload')}
              style={{
                backgroundColor: '#BEF264',
                color: '#09090B',
                border: 'none',
                padding: '8px 18px',
                borderRadius: '9999px',
                fontSize: '12.5px',
                fontWeight: '800',
                cursor: 'pointer',
                letterSpacing: '0.5px'
              }}
            >
              UPLOAD NOW
            </button>
            <UploadCloud size={28} color="#059669" />
          </div>
        </div>
      </div>

      {/* ANIMATED FILE FORMAT MARQUEE TICKER BANNER (Below Main 3 Cards) */}
      <style>{`
        @keyframes marqueeTicker {
          0% { transform: translateX(0%); }
          100% { transform: translateX(-50%); }
        }
      `}</style>

      <div style={{
        backgroundColor: '#FFFFFF',
        borderRadius: '24px',
        border: '1px solid #E2E8F0',
        boxShadow: '0 8px 30px rgba(0,0,0,0.02)',
        padding: '14px 20px',
        overflow: 'hidden',
        display: 'flex',
        alignItems: 'center',
        position: 'relative'
      }}>
        {/* Left Label Badge */}
        <div style={{
          backgroundColor: '#F8FAFC',
          border: '1px solid #E2E8F0',
          borderRadius: '12px',
          padding: '6px 14px',
          fontSize: '11px',
          fontWeight: '800',
          color: '#09090B',
          letterSpacing: '0.5px',
          textTransform: 'uppercase',
          zIndex: 2,
          marginRight: '16px',
          flexShrink: 0,
          boxShadow: '0 2px 8px rgba(0,0,0,0.03)'
        }}>
          Supported Formats
        </div>

        {/* Marquee Track Container */}
        <div style={{ overflow: 'hidden', flex: 1, position: 'relative' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            width: 'max-content',
            animation: 'marqueeTicker 28s linear infinite'
          }}>
            {[
              {
                name: 'PDF Documents', ext: '.pdf', color: '#EF4444',
                svg: (
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M14 2H6C4.89543 2 4 2.89543 4 4V20C4 21.1046 4.89543 22 6 22H18C19.1046 22 20 21.1046 20 20V8L14 2Z" fill="#DC2626" />
                    <path d="M14 2V8H20L14 2Z" fill="#FCA5A5" />
                    <text x="7" y="17" fill="white" fontSize="7" fontWeight="900" fontFamily="sans-serif">PDF</text>
                  </svg>
                )
              },
              {
                name: 'Word Documents', ext: '.docx, .doc', color: '#2563EB',
                svg: (
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M14 2H6C4.89543 2 4 2.89543 4 4V20C4 21.1046 4.89543 22 6 22H18C19.1046 22 20 21.1046 20 20V8L14 2Z" fill="#1D4ED8" />
                    <path d="M14 2V8H20L14 2Z" fill="#93C5FD" />
                    <text x="7" y="17" fill="white" fontSize="7" fontWeight="900" fontFamily="sans-serif">DOC</text>
                  </svg>
                )
              },
              {
                name: 'Excel Spreadsheets', ext: '.xlsx, .xls', color: '#10B981',
                svg: (
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M14 2H6C4.89543 2 4 2.89543 4 4V20C4 21.1046 4.89543 22 6 22H18C19.1046 22 20 21.1046 20 20V8L14 2Z" fill="#047857" />
                    <path d="M14 2V8H20L14 2Z" fill="#6EE7B7" />
                    <text x="7.5" y="17" fill="white" fontSize="7" fontWeight="900" fontFamily="sans-serif">XLS</text>
                  </svg>
                )
              },
              {
                name: 'CSV Datasets', ext: '.csv', color: '#0EA5E9',
                svg: (
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M14 2H6C4.89543 2 4 2.89543 4 4V20C4 21.1046 4.89543 22 6 22H18C19.1046 22 20 21.1046 20 20V8L14 2Z" fill="#0284C7" />
                    <path d="M14 2V8H20L14 2Z" fill="#7DD3FC" />
                    <text x="7" y="17" fill="white" fontSize="7" fontWeight="900" fontFamily="sans-serif">CSV</text>
                  </svg>
                )
              },
              {
                name: 'Text Files', ext: '.txt', color: '#334155',
                svg: (
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M14 2H6C4.89543 2 4 2.89543 4 4V20C4 21.1046 4.89543 22 6 22H18C19.1046 22 20 21.1046 20 20V8L14 2Z" fill="#1E293B" />
                    <path d="M14 2V8H20L14 2Z" fill="#94A3B8" />
                    <text x="7.5" y="17" fill="white" fontSize="7" fontWeight="900" fontFamily="sans-serif">TXT</text>
                  </svg>
                )
              },
              {
                name: 'Markdown Docs', ext: '.md', color: '#8B5CF6',
                svg: (
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M14 2H6C4.89543 2 4 2.89543 4 4V20C4 21.1046 4.89543 22 6 22H18C19.1046 22 20 21.1046 20 20V8L14 2Z" fill="#6D28D9" />
                    <path d="M14 2V8H20L14 2Z" fill="#C4B5FD" />
                    <text x="8" y="17" fill="white" fontSize="7" fontWeight="900" fontFamily="sans-serif">MD</text>
                  </svg>
                )
              },
              {
                name: 'PowerPoint Slides', ext: '.pptx, .ppt', color: '#F97316',
                svg: (
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M14 2H6C4.89543 2 4 2.89543 4 4V20C4 21.1046 4.89543 22 6 22H18C19.1046 22 20 21.1046 20 20V8L14 2Z" fill="#EA580C" />
                    <path d="M14 2V8H20L14 2Z" fill="#FDBA74" />
                    <text x="7.5" y="17" fill="white" fontSize="7" fontWeight="900" fontFamily="sans-serif">PPT</text>
                  </svg>
                )
              },
              {
                name: 'HTML Web Pages', ext: '.html, .htm', color: '#F59E0B',
                svg: (
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M14 2H6C4.89543 2 4 2.89543 4 4V20C4 21.1046 4.89543 22 6 22H18C19.1046 22 20 21.1046 20 20V8L14 2Z" fill="#D97706" />
                    <path d="M14 2V8H20L14 2Z" fill="#FDE68A" />
                    <text x="6" y="17" fill="white" fontSize="6.5" fontWeight="900" fontFamily="sans-serif">HTML</text>
                  </svg>
                )
              },
              {
                name: 'PNG Images', ext: '.png', color: '#06B6D4',
                svg: (
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M14 2H6C4.89543 2 4 2.89543 4 4V20C4 21.1046 4.89543 22 6 22H18C19.1046 22 20 21.1046 20 20V8L14 2Z" fill="#0891B2" />
                    <path d="M14 2V8H20L14 2Z" fill="#67E8F9" />
                    <text x="7" y="17" fill="white" fontSize="7" fontWeight="900" fontFamily="sans-serif">PNG</text>
                  </svg>
                )
              },
              {
                name: 'JPEG Images', ext: '.jpg, .jpeg', color: '#F43F5E',
                svg: (
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M14 2H6C4.89543 2 4 2.89543 4 4V20C4 21.1046 4.89543 22 6 22H18C19.1046 22 20 21.1046 20 20V8L14 2Z" fill="#E11D48" />
                    <path d="M14 2V8H20L14 2Z" fill="#FDA4AF" />
                    <text x="7" y="17" fill="white" fontSize="7" fontWeight="900" fontFamily="sans-serif">JPG</text>
                  </svg>
                )
              }
            ].concat([
              { name: 'PDF Documents', ext: '.pdf', color: '#EF4444', svg: <svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M14 2H6C4.89543 2 4 2.89543 4 4V20C4 21.1046 4.89543 22 6 22H18C19.1046 22 20 21.1046 20 20V8L14 2Z" fill="#DC2626" /><path d="M14 2V8H20L14 2Z" fill="#FCA5A5" /><text x="7" y="17" fill="white" fontSize="7" fontWeight="900">PDF</text></svg> },
              { name: 'Word Documents', ext: '.docx, .doc', color: '#2563EB', svg: <svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M14 2H6C4.89543 2 4 2.89543 4 4V20C4 21.1046 4.89543 22 6 22H18C19.1046 22 20 21.1046 20 20V8L14 2Z" fill="#1D4ED8" /><path d="M14 2V8H20L14 2Z" fill="#93C5FD" /><text x="7" y="17" fill="white" fontSize="7" fontWeight="900">DOC</text></svg> },
              { name: 'Excel Spreadsheets', ext: '.xlsx, .xls', color: '#10B981', svg: <svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M14 2H6C4.89543 2 4 2.89543 4 4V20C4 21.1046 4.89543 22 6 22H18C19.1046 22 20 21.1046 20 20V8L14 2Z" fill="#047857" /><path d="M14 2V8H20L14 2Z" fill="#6EE7B7" /><text x="7.5" y="17" fill="white" fontSize="7" fontWeight="900">XLS</text></svg> },
              { name: 'CSV Datasets', ext: '.csv', color: '#0EA5E9', svg: <svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M14 2H6C4.89543 2 4 2.89543 4 4V20C4 21.1046 4.89543 22 6 22H18C19.1046 22 20 21.1046 20 20V8L14 2Z" fill="#0284C7" /><path d="M14 2V8H20L14 2Z" fill="#7DD3FC" /><text x="7" y="17" fill="white" fontSize="7" fontWeight="900">CSV</text></svg> },
              { name: 'Text Files', ext: '.txt', color: '#334155', svg: <svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M14 2H6C4.89543 2 4 2.89543 4 4V20C4 21.1046 4.89543 22 6 22H18C19.1046 22 20 21.1046 20 20V8L14 2Z" fill="#1E293B" /><path d="M14 2V8H20L14 2Z" fill="#94A3B8" /><text x="7.5" y="17" fill="white" fontSize="7" fontWeight="900">TXT</text></svg> },
              { name: 'Markdown Docs', ext: '.md', color: '#8B5CF6', svg: <svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M14 2H6C4.89543 2 4 2.89543 4 4V20C4 21.1046 4.89543 22 6 22H18C19.1046 22 20 21.1046 20 20V8L14 2Z" fill="#6D28D9" /><path d="M14 2V8H20L14 2Z" fill="#C4B5FD" /><text x="8" y="17" fill="white" fontSize="7" fontWeight="900">MD</text></svg> },
              { name: 'PowerPoint Slides', ext: '.pptx, .ppt', color: '#F97316', svg: <svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M14 2H6C4.89543 2 4 2.89543 4 4V20C4 21.1046 4.89543 22 6 22H18C19.1046 22 20 21.1046 20 20V8L14 2Z" fill="#EA580C" /><path d="M14 2V8H20L14 2Z" fill="#FDBA74" /><text x="7.5" y="17" fill="white" fontSize="7" fontWeight="900">PPT</text></svg> },
              { name: 'HTML Web Pages', ext: '.html, .htm', color: '#F59E0B', svg: <svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M14 2H6C4.89543 2 4 2.89543 4 4V20C4 21.1046 4.89543 22 6 22H18C19.1046 22 20 21.1046 20 20V8L14 2Z" fill="#D97706" /><path d="M14 2V8H20L14 2Z" fill="#FDE68A" /><text x="6" y="17" fill="white" fontSize="6.5" fontWeight="900">HTML</text></svg> },
              { name: 'PNG Images', ext: '.png', color: '#06B6D4', svg: <svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M14 2H6C4.89543 2 4 2.89543 4 4V20C4 21.1046 4.89543 22 6 22H18C19.1046 22 20 21.1046 20 20V8L14 2Z" fill="#0891B2" /><path d="M14 2V8H20L14 2Z" fill="#67E8F9" /><text x="7" y="17" fill="white" fontSize="7" fontWeight="900">PNG</text></svg> },
              { name: 'JPEG Images', ext: '.jpg, .jpeg', color: '#F43F5E', svg: <svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M14 2H6C4.89543 2 4 2.89543 4 4V20C4 21.1046 4.89543 22 6 22H18C19.1046 22 20 21.1046 20 20V8L14 2Z" fill="#E11D48" /><path d="M14 2V8H20L14 2Z" fill="#FDA4AF" /><text x="7" y="17" fill="white" fontSize="7" fontWeight="900">JPG</text></svg> }
            ]).map((fmt, i) => (
              <div
                key={i}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '8px',
                  backgroundColor: '#F8FAFC',
                  border: '1px solid #E2E8F0',
                  borderRadius: '9999px',
                  padding: '6px 14px 6px 8px',
                  flexShrink: 0,
                  boxShadow: '0 2px 4px rgba(0,0,0,0.02)'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                  {fmt.svg}
                </div>
                <span style={{ fontSize: '12.5px', fontWeight: '700', color: '#09090B' }}>{fmt.name}</span>
                <span style={{ fontSize: '11px', color: '#64748B', fontWeight: '600' }}>({fmt.ext})</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Platform Guide & Documentation Banner */}
      <div style={{
        backgroundColor: '#F0F9FF',
        borderRadius: '24px',
        padding: '24px 32px',
        border: '1px solid #BAE6FD',
        boxShadow: '0 8px 30px rgba(14, 165, 233, 0.05)',
        display: 'flex',
        alignItems: 'center',
        justify: 'space-between',
        flexWrap: 'wrap',
        gap: '20px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ width: '44px', height: '44px', borderRadius: '14px', backgroundColor: '#0EA5E9', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <HelpCircle size={22} color="#FFFFFF" />
          </div>
          <div>
            <h4 style={{ fontSize: '16px', fontWeight: '800', color: '#0369A1', margin: 0 }}>Need help navigating WikiMind?</h4>
            <p style={{ fontSize: '13px', color: '#0284C7', margin: '2px 0 0 0' }}>Explore our step-by-step documentation, architecture guides, and platform FAQs.</p>
          </div>
        </div>
        <button
          onClick={() => setActiveTab('guide')}
          style={{
            backgroundColor: '#0EA5E9',
            color: '#FFFFFF',
            border: 'none',
            padding: '10px 22px',
            borderRadius: '9999px',
            fontSize: '13px',
            fontWeight: '700',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            boxShadow: '0 4px 12px rgba(14, 165, 233, 0.3)'
          }}
        >
          <span>Open Full Platform Guide</span>
          <ArrowRight size={14} />
        </button>
      </div>

      {/* Footer Component */}
      <Footer setActiveTab={setActiveTab} />

    </div>
  );
}
