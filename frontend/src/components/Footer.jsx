import React from 'react';
import { 
  Network, 
  BookOpen, 
  UploadCloud, 
  MessageSquare, 
  Github, 
  Layers,
  Globe,
  ExternalLink,
  Info,
  ShieldCheck,
  FileText
} from 'lucide-react';
import './Footer.css';

export default function Footer({ setActiveTab }) {
  return (
    <footer className="wikimind-footer">
      <div className="footer-ambient-glow" />

      {/* Top Main Grid */}
      <div className="footer-top-grid">
        
        {/* Column 1: Brand & Mission */}
        <div className="footer-brand-col">
          <div className="footer-logo-row">
            <img 
              src="/logo-color.png" 
              alt="WikiMind Logo" 
              className="footer-logo-img" 
            />
            <span className="footer-brand-title">WikiMind</span>
          </div>
          <p className="footer-tagline">
            An AI-powered personal knowledge base & interactive entity graph platform designed to structure documents into queryable wiki pages.
          </p>
        </div>

        {/* Column 2: Platform Navigation */}
        <div>
          <h4 className="footer-col-title">Platform</h4>
          <ul className="footer-links-list">
            <li className="footer-link-item" onClick={() => setActiveTab && setActiveTab('dashboard')}>
              <Layers size={14} />
              <span>Dashboard</span>
            </li>
            <li className="footer-link-item" onClick={() => setActiveTab && setActiveTab('upload')}>
              <UploadCloud size={14} />
              <span>Document Upload</span>
            </li>
            <li className="footer-link-item" onClick={() => setActiveTab && setActiveTab('wiki')}>
              <Network size={14} />
              <span>Knowledge Graph</span>
            </li>
            <li className="footer-link-item" onClick={() => setActiveTab && setActiveTab('chat')}>
              <MessageSquare size={14} />
              <span>Grounded AI Chat</span>
            </li>
            <li className="footer-link-item" onClick={() => setActiveTab && setActiveTab('guide')}>
              <BookOpen size={14} />
              <span>User Guide</span>
              <span className="footer-badge-pill">Docs</span>
            </li>
          </ul>
        </div>

        {/* Column 3: Project Info */}
        <div>
          <h4 className="footer-col-title">Project Info</h4>
          <ul className="footer-links-list">
            <li className="footer-link-item" onClick={() => setActiveTab && setActiveTab('guide')}>
              <Info size={14} />
              <span>Project Overview</span>
            </li>
            <li className="footer-link-item" onClick={() => setActiveTab && setActiveTab('upload')}>
              <FileText size={14} />
              <span>Document Ingestion</span>
            </li>
            <li className="footer-link-item" onClick={() => setActiveTab && setActiveTab('wiki')}>
              <Network size={14} />
              <span>Entity Extraction</span>
            </li>
            <li className="footer-link-item" onClick={() => setActiveTab && setActiveTab('chat')}>
              <MessageSquare size={14} />
              <span>Grounded QA Engine</span>
            </li>
            <li className="footer-link-item">
              <ShieldCheck size={14} />
              <span>Account Data Isolation</span>
            </li>
          </ul>
        </div>

        {/* Column 4: Author & Developer Resources */}
        <div>
          <h4 className="footer-col-title">Developer</h4>
          <ul className="footer-links-list">
            <li className="footer-link-item" onClick={() => window.open('https://www.jayashan.online/', '_blank', 'noopener,noreferrer')}>
              <Globe size={14} color="#60a5fa" />
              <span style={{ color: '#60a5fa', fontWeight: 600 }}>Jayashan Manodya</span>
              <ExternalLink size={12} color="#60a5fa" />
            </li>
            <li className="footer-link-item" onClick={() => setActiveTab && setActiveTab('guide')}>
              <BookOpen size={14} />
              <span>Platform Documentation</span>
            </li>
          </ul>
        </div>

      </div>

      <div className="footer-divider" />

      {/* Bottom Bar */}
      <div className="footer-bottom-row">
        <div>
          © {new Date().getFullYear()} WikiMind. Built by{' '}
          <a 
            href="https://www.jayashan.online/" 
            target="_blank" 
            rel="noopener noreferrer"
            style={{ color: '#60a5fa', textDecoration: 'none', fontWeight: 600 }}
          >
            Jayashan Manodya
          </a>
        </div>

        <div className="footer-bottom-links">
          <span className="footer-bottom-link" onClick={() => setActiveTab && setActiveTab('guide')}>
            Documentation
          </span>
          <span>•</span>
          <span className="footer-bottom-link">Privacy Policy</span>
          <span>•</span>
          <span style={{ color: '#94a3b8', fontWeight: 600 }}>v1.2.0</span>
        </div>
      </div>
    </footer>
  );
}
