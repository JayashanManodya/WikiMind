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
  HelpCircle
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
                display: 'flex',
                alignItems: 'center',
                justify: 'center'
              }}>
                <ArrowUpRight size={18} color="#FFFFFF" />
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
                  'https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=100&q=80',
                  'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?auto=format&fit=crop&w=100&q=80',
                  'https://images.unsplash.com/photo-1494790108377-be9c29b29330?auto=format&fit=crop&w=100&q=80'
                ].map((imgUrl, i) => (
                  <img
                    key={i}
                    src={imgUrl}
                    alt={`Avatar ${i + 1}`}
                    style={{
                      width: '32px',
                      height: '32px',
                      borderRadius: '50%',
                      objectFit: 'cover',
                      border: '2px solid #FFFFFF',
                      marginLeft: i === 0 ? 0 : '-10px',
                      boxShadow: '0 2px 6px rgba(0,0,0,0.1)'
                    }}
                  />
                ))}
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
          <HeroNodeGraph isLight={false} onNodeClick={() => setActiveTab('wiki')} />
        </div>

      </div>

      {/* BOTTOM BENTO ROW: 3 Distinct Bento Cards (Ref Image Layout) */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
        gap: '24px'
      }}>

        {/* BOTTOM CARD 1: White Card with Floating Badges matching Ref Image (Zero Boundary) */}
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
            backgroundColor: '#FF4D4D',
            color: '#FFFFFF',
            fontSize: '11px',
            fontWeight: '700',
            padding: '4px 12px',
            borderRadius: '9999px',
            transform: 'rotate(-6deg)',
            boxShadow: '0 4px 10px rgba(255, 77, 77, 0.3)'
          }}>
            Top rated RAG
          </div>

          {/* Floating badge pill 2 */}
          <div style={{
            position: 'absolute',
            top: '20px',
            right: '20px',
            backgroundColor: '#09090B',
            color: '#FFFFFF',
            fontSize: '11px',
            fontWeight: '700',
            padding: '4px 12px',
            borderRadius: '9999px',
            transform: 'rotate(8deg)',
            boxShadow: '0 4px 10px rgba(0, 0, 0, 0.2)'
          }}>
            Grounded AI
          </div>

          <div style={{ marginTop: '48px' }}>
            <h3 style={{ fontSize: '20px', fontWeight: '800', color: '#09090B', marginBottom: '8px', lineHeight: '1.25' }}>
              Grow your knowledge with zero boundary
            </h3>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12.5px', color: '#64748B', marginTop: '10px' }}>
              <ShieldCheck size={16} color="#10B981" />
              <span>Trusted by 50,000+ queries</span>
            </div>
          </div>

          <button
            onClick={() => setActiveTab('chat')}
            style={{
              marginTop: '20px',
              backgroundColor: '#09090B',
              color: '#FFFFFF',
              border: 'none',
              padding: '12px 20px',
              borderRadius: '16px',
              fontSize: '13px',
              fontWeight: '600',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justify: 'center',
              gap: '8px'
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
              <h3 style={{ fontSize: '18px', fontWeight: '700', color: '#09090B' }}>Explore Topics</h3>
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

        {/* BOTTOM CARD 3: Mint Soft Glow Box / Ingestion Feature matching Ref Image */}
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
              Multi-Format Parser
            </span>
            <h3 style={{ fontSize: '22px', fontWeight: '800', color: '#064E3B', marginTop: '14px', marginBottom: '8px', lineHeight: '1.2' }}>
              LlamaParse Document Platform!
            </h3>
            <p style={{ fontSize: '13px', color: '#047857', lineHeight: '1.5' }}>
              Upload PDFs, Word DOCX, and TXT files for deep layout OCR & structured Markdown generation.
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
              TRY NOW
            </button>
            <UploadCloud size={28} color="#059669" />
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
