import React, { useState, useEffect } from 'react';
import { 
  BookOpen, 
  Search, 
  Loader2,
  Share2,
  FileText,
  Network
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { getWikiPage } from '../api/client';
import KnowledgeGraphCanvas from '../components/KnowledgeGraphCanvas';
import NodePopover from '../components/NodePopover';
import { useAuth } from '../context/AuthContext';
import { useData } from '../context/DataContext';

export default function WikiPage({ selectedEntity, setSelectedEntity }) {
  const { user } = useAuth();
  const { wikiPages: cachedPages, wikiGraph: cachedGraph, loadWikiPages, loadWikiGraph, isLoadingWiki } = useData();

  const [activeEntity, setActiveEntity] = useState(selectedEntity || null);
  const [pageContent, setPageContent] = useState(null);
  const [viewMode, setViewMode] = useState('article'); // 'article' | 'graph'
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState('ALL');
  const [loadingPage, setLoadingPage] = useState(false);

  // State for Compact Floating Node Popover
  const [modalNode, setModalNode] = useState(null);

  useEffect(() => {
    loadWikiPages();
    loadWikiGraph();
  }, [user, loadWikiPages, loadWikiGraph]);

  const wikiPages = cachedPages || [];
  const graphData = cachedGraph || { nodes: [], edges: [] };
  const loadingList = isLoadingWiki;

  useEffect(() => {
    if (wikiPages.length > 0 && (!activeEntity || !wikiPages.some(p => p.entity_name === activeEntity))) {
      setActiveEntity(wikiPages[0].entity_name);
    }
  }, [wikiPages, activeEntity]);


  useEffect(() => {
    if (!activeEntity) return;

    const fetchPage = async () => {
      setLoadingPage(true);
      try {
        const res = await getWikiPage(activeEntity);
        setPageContent(res);
      } catch (err) {
        console.error("Wiki page fetch error:", err);
        setPageContent(null);
      } finally {
        setLoadingPage(false);
      }
    };
    fetchPage();
  }, [activeEntity]);

  const filteredPages = wikiPages.filter(page => {
    const matchesSearch = page.entity_name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesType = filterType === 'ALL' || page.entity_type === filterType;
    return matchesSearch && matchesType;
  });

  // Open compact popover anchored near clicked node position
  const handleNodeClickFromCanvas = (nodeId, nodeType, screenPos) => {
    setModalNode({
      entityName: nodeId,
      entityType: nodeType || 'CONCEPT',
      position: screenPos || { x: window.innerWidth / 2 - 135, y: window.innerHeight / 2 - 100 }
    });
  };

  // Switch to Article View when "View Detailed" button is clicked
  const handleViewDetailedFromModal = (entityName) => {
    setActiveEntity(entityName);
    if (setSelectedEntity) setSelectedEntity(entityName);
    setViewMode('article');
  };

  const [isMobile, setIsMobile] = useState(typeof window !== 'undefined' ? window.innerWidth < 768 : false);

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < 768);
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return (
    <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '260px 1fr', gap: '24px', width: '100%', minHeight: 'calc(100vh - 100px)' }}>
      
      {/* Compact Near-Node Popover Dialog */}
      {modalNode && (
        <NodePopover 
          entityName={modalNode.entityName}
          entityType={modalNode.entityType}
          position={modalNode.position}
          onClose={() => setModalNode(null)}
          onViewDetailed={handleViewDetailedFromModal}
        />
      )}

      {/* Left Sidebar: Entity Topic List (Hidden on Mobile while in Graph Mode to place Graph at Top) */}
      {(!isMobile || viewMode === 'article') && (
        <div style={{
          backgroundColor: '#FFFFFF',
          borderRadius: isMobile ? '20px' : '28px',
          border: '1px solid #E2E8F0',
          boxShadow: '0 10px 40px rgba(0,0,0,0.03)',
          padding: isMobile ? '16px' : '24px',
          display: 'flex',
          flexDirection: 'column',
          gap: isMobile ? '12px' : '18px',
          maxHeight: isMobile ? '240px' : '820px',
          overflowY: 'auto'
        }}>
        <div>
          <h3 style={{ fontSize: '15px', fontWeight: '600' }}>Wiki Knowledge Base</h3>
          <p style={{ fontSize: '11.5px', color: 'var(--text-muted)' }}>{wikiPages.length} topic pages</p>
        </div>

        {/* View Mode Switcher (Home Theme Segmented Pill Tabs) */}
        <div style={{ display: 'flex', backgroundColor: '#F1F5F9', padding: '4px', borderRadius: '14px', gap: '4px' }}>
          <button
            onClick={() => setViewMode('article')}
            style={{
              flex: 1,
              padding: '8px 12px',
              border: 'none',
              borderRadius: '10px',
              fontSize: '12px',
              fontWeight: viewMode === 'article' ? '700' : '600',
              backgroundColor: viewMode === 'article' ? '#FFFFFF' : 'transparent',
              color: viewMode === 'article' ? '#0F172A' : '#64748B',
              boxShadow: viewMode === 'article' ? '0 2px 8px rgba(0, 0, 0, 0.08)' : 'none',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px',
              transition: 'all 0.2s ease'
            }}
          >
            <FileText size={14} color={viewMode === 'article' ? '#2563EB' : '#64748B'} />
            <span>Article View</span>
          </button>
          <button
            onClick={() => setViewMode('graph')}
            style={{
              flex: 1,
              padding: '8px 12px',
              border: 'none',
              borderRadius: '10px',
              fontSize: '12px',
              fontWeight: viewMode === 'graph' ? '700' : '600',
              backgroundColor: viewMode === 'graph' ? '#FFFFFF' : 'transparent',
              color: viewMode === 'graph' ? '#0F172A' : '#64748B',
              boxShadow: viewMode === 'graph' ? '0 2px 8px rgba(0, 0, 0, 0.08)' : 'none',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px',
              transition: 'all 0.2s ease'
            }}
          >
            <Network size={14} color={viewMode === 'graph' ? '#2563EB' : '#64748B'} />
            <span>Graph View</span>
          </button>
        </div>

        {/* Search Bar */}
        <div style={{ position: 'relative' }}>
          <Search size={14} color="var(--text-muted)" style={{ position: 'absolute', left: '10px', top: '10px' }} />
          <input 
            type="text" 
            placeholder="Search topic..." 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              width: '100%',
              padding: '8px 10px 8px 30px',
              backgroundColor: 'var(--bg-input)',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius-md)',
              color: 'var(--text-main)',
              fontSize: '12.5px',
              outline: 'none'
            }}
          />
        </div>

        {/* Filter Pills */}
        <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
          {['ALL', 'ORGANIZATION', 'PERSON', 'CONCEPT', 'TECHNOLOGY'].map(type => (
            <button
              key={type}
              onClick={() => setFilterType(type)}
              style={{
                backgroundColor: filterType === type ? '#09090B' : '#F4F4F5',
                color: filterType === type ? '#FFFFFF' : '#3F3F46',
                border: 'none',
                padding: '3px 8px',
                borderRadius: '4px',
                fontSize: '10.5px',
                fontWeight: '500',
                cursor: 'pointer'
              }}
            >
              {type}
            </button>
          ))}
        </div>

        {/* List Items */}
        {loadingList ? (
          <div style={{ padding: '20px', textAlign: 'center' }}>
            <Loader2 className="spin" size={20} color="#09090B" style={{ animation: 'spin 1s linear infinite' }} />
          </div>
        ) : filteredPages.length === 0 ? (
          <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>No topics found.</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {filteredPages.map((page, idx) => {
              const isActive = activeEntity === page.entity_name;
              return (
                <div
                  key={idx}
                  onClick={() => {
                    setActiveEntity(page.entity_name);
                    if (setSelectedEntity) setSelectedEntity(page.entity_name);
                  }}
                  style={{
                    padding: '10px 12px',
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: isActive ? '#09090B' : 'transparent',
                    color: isActive ? '#FFFFFF' : 'var(--text-main)',
                    border: '1px solid',
                    borderColor: isActive ? '#09090B' : 'transparent',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <p style={{ fontSize: '13px', fontWeight: isActive ? '600' : '500' }}>
                      {page.entity_name}
                    </p>
                    <span className={isActive ? 'badge-dark' : 'badge-clean'} style={{ fontSize: '9.5px' }}>
                      {page.entity_type || 'CONCEPT'}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
      )}

      {/* Main Panel */}
      <div style={{ backgroundColor: '#FFFFFF', borderRadius: isMobile ? '20px' : '28px', border: '1px solid #E2E8F0', boxShadow: '0 8px 30px rgba(0,0,0,0.02)', padding: isMobile ? '16px 14px' : '32px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
        
        {viewMode === 'graph' ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ borderBottom: '1px solid var(--border-color)', paddingBottom: '14px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
              <div>
                <h1 style={{ fontSize: isMobile ? '18px' : '22px', fontWeight: '700', color: '#09090B' }}>Interactive Knowledge Graph Network</h1>
                <p style={{ fontSize: '12.5px', color: 'var(--text-muted)' }}>
                  Click any circular node to open near-node summary popover & detailed article.
                </p>
              </div>
              <button className="btn btn-outline" onClick={() => setViewMode('article')}>
                <BookOpen size={14} />
                <span>Article View</span>
              </button>
            </div>

            {/* Interactive Force-Directed Canvas */}
            <KnowledgeGraphCanvas 
              graphData={graphData} 
              wikiPages={wikiPages}
              onSelectNode={handleNodeClickFromCanvas} 
            />
          </div>
        ) : loadingPage ? (
          <div style={{ padding: '60px', textAlign: 'center' }}>
            <Loader2 className="spin" size={28} color="#09090B" style={{ animation: 'spin 1s linear infinite' }} />
            <p style={{ marginTop: '10px', fontSize: '13px', color: 'var(--text-muted)' }}>Loading Wiki Topic Page...</p>
          </div>
        ) : !pageContent ? (
          <div style={{ padding: '60px', textAlign: 'center', color: 'var(--text-muted)' }}>
            <BookOpen size={40} color="var(--border-color)" style={{ marginBottom: '10px' }} />
            <p style={{ fontSize: '13px' }}>Select a topic page from the left sidebar to read article.</p>
          </div>
        ) : (
          <div>
            {/* Page Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-color)', paddingBottom: '14px', marginBottom: '20px' }}>
              <div>
                <h1 style={{ fontSize: '24px', fontWeight: '700', color: '#09090B' }}>{pageContent.entity_name}</h1>
                <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>File: {pageContent.filename}</p>
              </div>
              <button className="btn btn-outline" onClick={() => setViewMode('graph')}>
                <Share2 size={14} />
                <span>View Knowledge Graph</span>
              </button>
            </div>

            {/* Markdown Render Body */}
            <div className="markdown-body">
              <ReactMarkdown>
                {pageContent.content}
              </ReactMarkdown>
            </div>
          </div>
        )}
      </div>

    </div>
  );
}
