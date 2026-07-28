import React, { useState, useEffect } from 'react';
import { 
  BookOpen, 
  Search, 
  Loader2,
  FileText
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { getWikiIndex, getWikiPage } from '../api/client';

export default function WikiPage({ selectedEntity, setSelectedEntity }) {
  const [wikiPages, setWikiPages] = useState([]);
  const [activeEntity, setActiveEntity] = useState(selectedEntity || null);
  const [pageContent, setPageContent] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState('ALL');
  const [loadingList, setLoadingList] = useState(true);
  const [loadingPage, setLoadingPage] = useState(false);

  useEffect(() => {
    const fetchIndex = async () => {
      try {
        const res = await getWikiIndex();
        if (res.pages && res.pages.length > 0) {
          setWikiPages(res.pages);
          if (!activeEntity) {
            setActiveEntity(res.pages[0].entity_name);
          }
        }
      } catch (err) {
        console.error("Wiki index fetch error:", err);
      } finally {
        setLoadingList(false);
      }
    };
    fetchIndex();
  }, []);

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

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: '20px', minHeight: 'calc(100vh - 140px)' }}>
      
      {/* Left Sidebar: Entity Topic List */}
      <div className="clean-card" style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '14px', maxHeight: '800px', overflowY: 'auto' }}>
        <div>
          <h3 style={{ fontSize: '15px', fontWeight: '600' }}>Wiki Knowledge Base</h3>
          <p style={{ fontSize: '11.5px', color: 'var(--text-muted)' }}>{wikiPages.length} topic pages</p>
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
                      {page.entity_type}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Main Panel: Markdown Content Viewer */}
      <div className="clean-card" style={{ padding: '28px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {loadingPage ? (
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
              <span className="badge-clean">{pageContent.internal_links?.length || 0} Connected Links</span>
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
