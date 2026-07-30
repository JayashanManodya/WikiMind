import React, { useRef, useEffect, useState, useMemo } from 'react';
import { Maximize2, Minimize2, ZoomIn, ZoomOut, RefreshCw, Search, Layers, Info } from 'lucide-react';

const FILE_COLOR_PALETTE = [
  '#2563EB', // Royal Blue
  '#F97316', // Vibrant Orange
  '#10B981', // Emerald Green
  '#8B5CF6', // Purple
  '#EF4444', // Red
  '#06B6D4', // Cyan
  '#EC4899', // Pink
  '#EAB308', // Amber Gold
  '#6366F1', // Indigo
  '#14B8A6', // Teal
  '#F43F5E', // Rose
  '#A855F7'  // Violet
];

const getFileColor = (fileKey) => {
  if (!fileKey) return FILE_COLOR_PALETTE[0];
  let hash = 0;
  for (let i = 0; i < fileKey.length; i++) {
    hash = fileKey.charCodeAt(i) + ((hash << 5) - hash);
  }
  const index = Math.abs(hash) % FILE_COLOR_PALETTE.length;
  return FILE_COLOR_PALETTE[index];
};

export default function KnowledgeGraphCanvas({ graphData, wikiPages = [], onSelectNode }) {
  const canvasRef = useRef(null);
  const containerRef = useRef(null);

  const [isFullscreen, setIsFullscreen] = useState(false);
  const [hoveredNode, setHoveredNode] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [activeCommunityFilter, setActiveCommunityFilter] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');

  // Map each wiki page title to its source document filename
  const pageFileMap = useMemo(() => {
    const map = {};
    if (wikiPages && wikiPages.length > 0) {
      wikiPages.forEach(p => {
        if (p.entity_name) {
          map[p.entity_name.toLowerCase()] = p.filename || 'Ingested Document';
        }
      });
    }
    return map;
  }, [wikiPages]);

  // Compute communities / source files summary for legend
  const communities = useMemo(() => {
    const communityMap = {};

    // 1. Process wikiPages first to get true source document list & wiki counts
    if (wikiPages && wikiPages.length > 0) {
      wikiPages.forEach(p => {
        const fileKey = p.filename || 'Ingested Document';
        if (!communityMap[fileKey]) {
          communityMap[fileKey] = {
            name: fileKey,
            color: getFileColor(fileKey),
            count: 0
          };
        }
        communityMap[fileKey].count += 1;
      });
    }

    // 2. Process graph nodes if missing
    if (graphData && graphData.nodes) {
      graphData.nodes.forEach(n => {
        const fileKey = n.filename || n.file || pageFileMap[n.id?.toLowerCase()] || 'Ingested Document';
        if (!communityMap[fileKey]) {
          communityMap[fileKey] = {
            name: fileKey,
            color: getFileColor(fileKey),
            count: 1
          };
        }
      });
    }

    return Object.values(communityMap).sort((a, b) => b.count - a.count);
  }, [graphData, wikiPages, pageFileMap]);

  // Pan & Zoom state
  const transformRef = useRef({ x: 0, y: 0, scale: 1 });
  const isDraggingBg = useRef(false);
  const dragStart = useRef({ x: 0, y: 0 });

  // Physics nodes & edges state
  const nodesRef = useRef([]);
  const edgesRef = useRef([]);
  const draggedNodeRef = useRef(null);
  const animationFrameRef = useRef(null);

  // Initialize nodes and edges physics positions
  useEffect(() => {
    if (!graphData || !graphData.nodes || graphData.nodes.length === 0) {
      nodesRef.current = [];
      edgesRef.current = [];
      return;
    }

    const rawNodes = graphData.nodes;
    const rawEdges = graphData.edges || [];

    // Calculate node degree (number of links)
    const degreeMap = {};
    rawNodes.forEach(n => { degreeMap[n.id] = 0; });
    rawEdges.forEach(e => {
      if (degreeMap[e.source] !== undefined) degreeMap[e.source] += 1;
      if (degreeMap[e.target] !== undefined) degreeMap[e.target] += 1;
    });

    const width = 700;
    const height = 550;

    // Layout nodes in a circle initially with random jitter
    const count = rawNodes.length;
    const radius = Math.min(width, height) * 0.35;

    const initializedNodes = rawNodes.map((n, i) => {
      const angle = (i / count) * 2 * Math.PI;
      const deg = degreeMap[n.id] || 1;
      const fileKey = n.filename || n.file || pageFileMap[n.id?.toLowerCase()] || 'Ingested Document';
      const color = getFileColor(fileKey);

      return {
        id: n.id,
        label: n.label || n.id,
        type: n.type || 'CONCEPT',
        fileKey: fileKey,
        color: color,
        degree: deg,
        r: Math.min(36, Math.max(16, 14 + deg * 3.5)), // Node radius based on degree
        x: width / 2 + radius * Math.cos(angle) + (Math.random() - 0.5) * 40,
        y: height / 2 + radius * Math.sin(angle) + (Math.random() - 0.5) * 40,
        vx: 0,
        vy: 0
      };
    });

    // Map edges to node references
    const nodeMap = {};
    initializedNodes.forEach(n => { nodeMap[n.id] = n; });

    const initializedEdges = [];
    rawEdges.forEach(e => {
      const srcNode = nodeMap[e.source];
      const tgtNode = nodeMap[e.target];
      if (srcNode && tgtNode) {
        initializedEdges.push({
          source: srcNode,
          target: tgtNode,
          relation: e.relation || 'RELATED'
        });
      }
    });

    nodesRef.current = initializedNodes;
    edgesRef.current = initializedEdges;

    // Center transform
    transformRef.current = { x: 0, y: 0, scale: 1 };
  }, [graphData, pageFileMap]);

  // Main Physics Simulation & Canvas Rendering Loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    let isRunning = true;

    const simulateAndRender = () => {
      if (!isRunning) return;

      const nodes = nodesRef.current;
      const edges = edgesRef.current;
      const width = canvas.width;
      const height = canvas.height;

      // 1. Force Simulation Step
      if (nodes.length > 0) {
        const kRepulsion = 4500;
        const linkDistance = 140;
        const kLink = 0.04;
        const damping = 0.86;
        const gravity = 0.015;
        const center = { x: width / 2, y: height / 2 };

        // Repulsion between all node pairs
        for (let i = 0; i < nodes.length; i++) {
          for (let j = i + 1; j < nodes.length; j++) {
            const n1 = nodes[i];
            const n2 = nodes[j];

            let dx = n2.x - n1.x;
            let dy = n2.y - n1.y;
            let dist = Math.sqrt(dx * dx + dy * dy) || 1;

            if (dist < 400) {
              const force = kRepulsion / (dist * dist);
              const fx = (dx / dist) * force;
              const fy = (dy / dist) * force;

              if (n1 !== draggedNodeRef.current) {
                n1.vx -= fx;
                n1.vy -= fy;
              }
              if (n2 !== draggedNodeRef.current) {
                n2.vx += fx;
                n2.vy += fy;
              }
            }
          }
        }

        // Link Attraction between connected nodes
        edges.forEach(e => {
          const n1 = e.source;
          const n2 = e.target;

          let dx = n2.x - n1.x;
          let dy = n2.y - n1.y;
          let dist = Math.sqrt(dx * dx + dy * dy) || 1;

          const force = (dist - linkDistance) * kLink;
          const fx = (dx / dist) * force;
          const fy = (dy / dist) * force;

          if (n1 !== draggedNodeRef.current) {
            n1.vx += fx;
            n1.vy += fy;
          }
          if (n2 !== draggedNodeRef.current) {
            n2.vx -= fx;
            n2.vy -= fy;
          }
        });

        // Gravity pull toward canvas center & position update
        nodes.forEach(n => {
          if (n !== draggedNodeRef.current) {
            n.vx += (center.x - n.x) * gravity;
            n.vy += (center.y - n.y) * gravity;

            n.vx *= damping;
            n.vy *= damping;

            n.x += n.vx;
            n.y += n.vy;
          }
        });
      }

      // 2. Render Frame
      ctx.clearRect(0, 0, width, height);

      // Save context for Pan & Zoom
      ctx.save();
      const t = transformRef.current;
      ctx.translate(t.x, t.y);
      ctx.scale(t.scale, t.scale);

      const searchLower = searchQuery.toLowerCase().trim();

      // Render Edges with directional arrows using source node colors
      edges.forEach(e => {
        const n1 = e.source;
        const n2 = e.target;

        const dx = n2.x - n1.x;
        const dy = n2.y - n1.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;

        let isDimmed = false;
        if (activeCommunityFilter && n1.fileKey !== activeCommunityFilter && n2.fileKey !== activeCommunityFilter) {
          isDimmed = true;
        }
        if (searchLower && !n1.label.toLowerCase().includes(searchLower) && !n2.label.toLowerCase().includes(searchLower)) {
          isDimmed = true;
        }

        // Start/End points at node borders
        const startX = n1.x + (dx / dist) * n1.r;
        const startY = n1.y + (dy / dist) * n1.r;
        const endX = n2.x - (dx / dist) * n2.r;
        const endY = n2.y - (dy / dist) * n2.r;

        ctx.save();
        ctx.globalAlpha = isDimmed ? 0.12 : 0.45;

        ctx.beginPath();
        ctx.moveTo(startX, startY);
        ctx.lineTo(endX, endY);
        ctx.strokeStyle = n1.color || '#2563EB';
        ctx.lineWidth = isDimmed ? 1 : 1.8;
        ctx.stroke();

        // Render small arrowhead at target
        const arrowSize = 7;
        const angle = Math.atan2(dy, dx);

        ctx.beginPath();
        ctx.moveTo(endX, endY);
        ctx.lineTo(
          endX - arrowSize * Math.cos(angle - Math.PI / 6),
          endY - arrowSize * Math.sin(angle - Math.PI / 6)
        );
        ctx.lineTo(
          endX - arrowSize * Math.cos(angle + Math.PI / 6),
          endY - arrowSize * Math.sin(angle + Math.PI / 6)
        );
        ctx.closePath();
        ctx.fillStyle = n1.color || '#2563EB';
        ctx.fill();

        ctx.restore();
      });

      // Render Solid Colored Nodes (No White Outline)
      nodes.forEach(n => {
        const isHovered = hoveredNode && hoveredNode.id === n.id;
        const isSelected = selectedNode && selectedNode.id === n.id;
        let isDimmed = false;
        
        if (activeCommunityFilter && n.fileKey !== activeCommunityFilter) {
          isDimmed = true;
        }
        if (searchLower && !n.label.toLowerCase().includes(searchLower)) {
          isDimmed = true;
        }

        ctx.save();
        ctx.globalAlpha = isDimmed ? 0.15 : 1;

        ctx.beginPath();
        ctx.arc(n.x, n.y, n.r, 0, 2 * Math.PI);

        // Solid node fill color based on file palette
        ctx.fillStyle = n.color || '#2563EB';

        // Outer Glow Shadow on hover/selection (No white outline stroke)
        if (isHovered || isSelected || (activeCommunityFilter && n.fileKey === activeCommunityFilter) || (searchLower && n.label.toLowerCase().includes(searchLower))) {
          ctx.shadowColor = n.color;
          ctx.shadowBlur = isSelected ? 22 : 16;
        }

        ctx.fill();

        // Text label inside / centered over node (Solid Black)
        ctx.font = `800 ${Math.min(13, Math.max(10, n.r * 0.55))}px Inter, sans-serif`;
        ctx.fillStyle = '#000000';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        
        // Wrap text if needed
        const maxTextWidth = n.r * 1.7;
        let text = n.label;
        if (ctx.measureText(text).width > maxTextWidth && text.length > 10) {
          text = text.substring(0, 8) + '..';
        }
        ctx.fillText(text, n.x, n.y);

        ctx.restore();
      });

      ctx.restore();

      animationFrameRef.current = requestAnimationFrame(simulateAndRender);
    };

    simulateAndRender();

    return () => {
      isRunning = false;
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [hoveredNode, selectedNode, activeCommunityFilter, searchQuery]);

  // Handle Resize
  useEffect(() => {
    const handleResize = () => {
      const canvas = canvasRef.current;
      const container = containerRef.current;
      if (canvas && container) {
        canvas.width = container.clientWidth - (isFullscreen ? 300 : 280);
        canvas.height = container.clientHeight || 580;
      }
    };
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [isFullscreen]);

  // Convert mouse coordinates to canvas world coordinates
  const getCanvasCoords = (e) => {
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    const clientX = e.clientX || (e.touches && e.touches[0].clientX);
    const clientY = e.clientY || (e.touches && e.touches[0].clientY);

    const screenX = clientX - rect.left;
    const screenY = clientY - rect.top;

    const t = transformRef.current;
    const worldX = (screenX - t.x) / t.scale;
    const worldY = (screenY - t.y) / t.scale;

    return { screenX, screenY, worldX, worldY };
  };

  // Find node under mouse position
  const findNodeAt = (worldX, worldY) => {
    const nodes = nodesRef.current;
    for (let i = nodes.length - 1; i >= 0; i--) {
      const n = nodes[i];
      const dx = worldX - n.x;
      const dy = worldY - n.y;
      if (dx * dx + dy * dy <= n.r * n.r) {
        return n;
      }
    }
    return null;
  };

  // Mouse Interaction Events
  const handleMouseDown = (e) => {
    const { screenX, screenY, worldX, worldY } = getCanvasCoords(e);
    const node = findNodeAt(worldX, worldY);

    if (node) {
      draggedNodeRef.current = node;
      node.vx = 0;
      node.vy = 0;
    } else {
      isDraggingBg.current = true;
      dragStart.current = { x: screenX - transformRef.current.x, y: screenY - transformRef.current.y };
    }
  };

  const handleMouseMove = (e) => {
    const { screenX, screenY, worldX, worldY } = getCanvasCoords(e);

    if (draggedNodeRef.current) {
      draggedNodeRef.current.x = worldX;
      draggedNodeRef.current.y = worldY;
      draggedNodeRef.current.vx = 0;
      draggedNodeRef.current.vy = 0;
    } else if (isDraggingBg.current) {
      transformRef.current.x = screenX - dragStart.current.x;
      transformRef.current.y = screenY - dragStart.current.y;
    } else {
      const node = findNodeAt(worldX, worldY);
      setHoveredNode(node);
    }
  };

  const handleMouseUp = (e) => {
    const { screenX, screenY, worldX, worldY } = getCanvasCoords(e);
    const canvas = canvasRef.current;
    const rect = canvas ? canvas.getBoundingClientRect() : { left: 0, top: 0 };
    const node = draggedNodeRef.current || findNodeAt(worldX, worldY);

    if (node) {
      setSelectedNode(node);
      
      const absoluteScreenX = rect.left + screenX;
      const absoluteScreenY = rect.top + screenY;

      if (onSelectNode) {
        onSelectNode(node.id, node.type, { x: absoluteScreenX, y: absoluteScreenY });
      }
      draggedNodeRef.current = null;
    }
    isDraggingBg.current = false;
  };

  // Mouse Wheel Zoom
  const handleWheel = (e) => {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9;
    const { screenX, screenY } = getCanvasCoords(e);

    const t = transformRef.current;
    const newScale = Math.min(3.5, Math.max(0.3, t.scale * zoomFactor));

    t.x = screenX - (screenX - t.x) * (newScale / t.scale);
    t.y = screenY - (screenY - t.y) * (newScale / t.scale);
    t.scale = newScale;
  };

  // Zoom controls
  const zoomIn = () => {
    transformRef.current.scale = Math.min(3.5, transformRef.current.scale * 1.25);
  };
  const zoomOut = () => {
    transformRef.current.scale = Math.max(0.3, transformRef.current.scale * 0.8);
  };
  const resetZoom = () => {
    transformRef.current = { x: 0, y: 0, scale: 1 };
  };

  const activeDisplayNode = hoveredNode || selectedNode;

  return (
    <div 
      ref={containerRef} 
      style={{ 
        position: 'relative', 
        width: '100%', 
        height: isFullscreen ? '100vh' : '580px', 
        backgroundColor: '#FFFFFF', // Pure Light Theme Canvas Background
        borderRadius: '24px', 
        border: '1px solid #E2E8F0', 
        overflow: 'hidden',
        display: 'flex',
        boxShadow: '0 8px 30px rgba(0,0,0,0.02)',
        ...(isFullscreen ? { position: 'fixed', top: 0, left: 0, zIndex: 9999, borderRadius: 0 } : {})
      }}
    >
      {/* Main Canvas Viewport (Left Area - Light Theme) */}
      <div style={{ flex: 1, position: 'relative', height: '100%', overflow: 'hidden' }}>
        <canvas 
          ref={canvasRef} 
          onMouseDown={handleMouseDown} 
          onMouseMove={handleMouseMove} 
          onMouseUp={handleMouseUp} 
          onWheel={handleWheel} 
          style={{ width: '100%', height: '100%', cursor: hoveredNode ? 'pointer' : 'grab' }}
        />

        {/* Top Floating Control Toolbar (Light Theme) */}
        <div style={{ position: 'absolute', top: '16px', left: '16px', display: 'flex', gap: '8px', zIndex: 10 }}>
          <button 
            onClick={zoomIn} 
            title="Zoom In"
            style={{ width: '36px', height: '36px', borderRadius: '10px', backgroundColor: '#FFFFFF', border: '1px solid #E2E8F0', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', boxShadow: '0 2px 8px rgba(0,0,0,0.05)' }}
          >
            <ZoomIn size={16} color="#09090B" />
          </button>

          <button 
            onClick={zoomOut} 
            title="Zoom Out"
            style={{ width: '36px', height: '36px', borderRadius: '10px', backgroundColor: '#FFFFFF', border: '1px solid #E2E8F0', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', boxShadow: '0 2px 8px rgba(0,0,0,0.05)' }}
          >
            <ZoomOut size={16} color="#09090B" />
          </button>

          <button 
            onClick={resetZoom} 
            title="Reset View"
            style={{ width: '36px', height: '36px', borderRadius: '10px', backgroundColor: '#FFFFFF', border: '1px solid #E2E8F0', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', boxShadow: '0 2px 8px rgba(0,0,0,0.05)' }}
          >
            <RefreshCw size={15} color="#09090B" />
          </button>

          <button 
            onClick={() => setIsFullscreen(!isFullscreen)} 
            title={isFullscreen ? "Exit Fullscreen" : "Fullscreen"}
            style={{ width: '36px', height: '36px', borderRadius: '10px', backgroundColor: '#09090B', border: 'none', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', boxShadow: '0 2px 8px rgba(0,0,0,0.12)' }}
          >
            {isFullscreen ? <Minimize2 size={16} color="#FFFFFF" /> : <Maximize2 size={16} color="#FFFFFF" />}
          </button>
        </div>
      </div>

      {/* Right Inspector Sidebar Panel (Clean Light Theme) */}
      <div style={{
        width: '280px',
        backgroundColor: '#FFFFFF',
        borderLeft: '1px solid #E2E8F0',
        padding: '18px 16px',
        display: 'flex',
        flexDirection: 'column',
        gap: '20px',
        overflowY: 'auto',
        zIndex: 10
      }}>
        
        {/* 1. Search Nodes Input */}
        <div>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            backgroundColor: '#F8FAFC',
            borderRadius: '10px',
            padding: '8px 12px',
            border: '1px solid #E2E8F0'
          }}>
            <Search size={15} color="#64748B" />
            <input
              type="text"
              placeholder="Search nodes..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                backgroundColor: 'transparent',
                border: 'none',
                outline: 'none',
                fontSize: '12.5px',
                color: '#09090B',
                width: '100%'
              }}
            />
          </div>
        </div>

        {/* 2. NODE INFO Card */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', backgroundColor: '#F8FAFC', padding: '14px', borderRadius: '12px', border: '1px solid #E2E8F0' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Info size={13} color="#2563EB" />
            <span style={{ fontSize: '11px', fontWeight: '800', color: '#64748B', letterSpacing: '0.5px', textTransform: 'uppercase' }}>
              NODE INFO
            </span>
          </div>

          {activeDisplayNode ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginTop: '4px' }}>
              <p style={{ fontSize: '14px', fontWeight: '700', color: '#09090B', margin: 0 }}>
                {activeDisplayNode.label}
              </p>
              <div style={{ fontSize: '11.5px', color: '#64748B', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                <p style={{ margin: 0 }}>Type: <span style={{ color: '#09090B', fontWeight: '600' }}>{activeDisplayNode.type}</span></p>
                <p style={{ margin: 0 }}>Source: <span style={{ color: activeDisplayNode.color, fontWeight: '700' }}>{activeDisplayNode.fileKey}</span></p>
                <p style={{ margin: 0 }}>Connections: <span style={{ color: '#09090B', fontWeight: '600' }}>{activeDisplayNode.degree}</span></p>
              </div>
            </div>
          ) : (
            <p style={{ fontSize: '12px', color: '#94A3B8', fontStyle: 'italic', margin: 0 }}>
              Click or hover a node to inspect it
            </p>
          )}
        </div>

        {/* 3. SOURCE FILES & COMMUNITIES List */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Layers size={13} color="#2563EB" />
            <span style={{ fontSize: '11px', fontWeight: '800', color: '#64748B', letterSpacing: '0.5px', textTransform: 'uppercase' }}>
              SOURCE FILES & COMMUNITIES
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {communities.map((c) => {
              const isSelectedFilter = activeCommunityFilter === c.name;
              return (
                <div
                  key={c.name}
                  onMouseEnter={() => setActiveCommunityFilter(c.name)}
                  onMouseLeave={() => setActiveCommunityFilter(null)}
                  onClick={() => setActiveCommunityFilter(prev => prev === c.name ? null : c.name)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justify: 'space-between',
                    padding: '8px 10px',
                    borderRadius: '8px',
                    backgroundColor: isSelectedFilter ? '#F1F5F9' : 'transparent',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', overflow: 'hidden' }}>
                    <div style={{
                      width: '10px',
                      height: '10px',
                      borderRadius: '9999px',
                      backgroundColor: c.color,
                      flexShrink: 0,
                      boxShadow: `0 0 6px ${c.color}`
                    }} />
                    <span style={{
                      fontSize: '12px',
                      fontWeight: isSelectedFilter ? '700' : '500',
                      color: isSelectedFilter ? '#09090B' : '#334155',
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis'
                    }}>
                      {c.name}
                    </span>
                  </div>
                  <span style={{ fontSize: '11px', fontWeight: '700', color: c.color, marginLeft: '6px', flexShrink: 0 }}>
                    {c.count} wikis
                  </span>
                </div>
              );
            })}
          </div>
        </div>

      </div>
    </div>
  );
}
