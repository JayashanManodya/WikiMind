import React, { useRef, useEffect } from 'react';

export default function HeroNodeGraph({ onNodeClick, isLight = true }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    let animationFrameId;
    let width = (canvas.width = canvas.parentElement.clientWidth || 450);
    let height = (canvas.height = 360);

    const handleResize = () => {
      if (canvas.parentElement) {
        width = canvas.width = canvas.parentElement.clientWidth;
        height = canvas.height = 360;
      }
    };
    window.addEventListener('resize', handleResize);

    // 4 Primary File Format Nodes + Central Hub + Auxiliary Graph Nodes
    const initialNodes = [
      // 4 Main File Format Nodes
      { x: width * 0.22, y: height * 0.28, r: 34, vx: 0.25, vy: 0.15, label: 'PDF', subtext: 'DOC', format: 'pdf', gradient: ['#F87171', '#EF4444', '#DC2626'] },
      { x: width * 0.78, y: height * 0.25, r: 34, vx: -0.2, vy: 0.2, label: 'WORD', subtext: 'DOCX', format: 'word', gradient: ['#60A5FA', '#2563EB', '#1D4ED8'] },
      { x: width * 0.22, y: height * 0.72, r: 34, vx: 0.15, vy: -0.2, label: 'EXCEL', subtext: 'XLSX', format: 'excel', gradient: ['#34D399', '#10B981', '#047857'] },
      { x: width * 0.78, y: height * 0.72, r: 34, vx: -0.25, vy: -0.15, label: 'CSV', subtext: 'DATA', format: 'csv', gradient: ['#38BDF8', '#0EA5E9', '#0369A1'] },
      
      // Central WikiMind Knowledge Engine Hub
      { x: width * 0.50, y: height * 0.48, r: 38, vx: 0.1, vy: -0.1, label: 'WikiMind', subtext: 'GRAPH', format: 'hub', gradient: ['#A78BFA', '#7C3AED', '#5B21B6'] },
      
      // Supporting Feature Nodes
      { x: width * 0.50, y: height * 0.18, r: 20, vx: -0.15, vy: 0.1, label: 'Vectors', format: 'aux', gradient: ['#93C5FD', '#3B82F6', '#1D4ED8'] },
      { x: width * 0.50, y: height * 0.82, r: 22, vx: 0.15, vy: -0.1, label: 'Graph RAG', format: 'aux', gradient: ['#FDE047', '#EAB308', '#CA8A04'] },
      { x: width * 0.08, y: height * 0.50, r: 18, vx: 0.1, vy: 0.15, label: 'Entities', format: 'aux', gradient: ['#F472B6', '#EC4899', '#BE185D'] },
      { x: width * 0.92, y: height * 0.50, r: 18, vx: -0.1, vy: -0.15, label: 'AI QA', format: 'aux', gradient: ['#38BDF8', '#0284C7', '#0369A1'] },
    ];

    // Connections linking PDF, WORD, EXCEL, CSV to central WikiMind Hub & Features
    const links = [
      [0, 4], [1, 4], [2, 4], [3, 4], // 4 File Formats -> WikiMind Hub
      [0, 5], [1, 5],                 // PDF & WORD -> Vectors
      [2, 6], [3, 6],                 // EXCEL & CSV -> Graph RAG
      [0, 7], [2, 7],                 // PDF & EXCEL -> Entities
      [1, 8], [3, 8],                 // WORD & CSV -> AI QA
      [5, 4], [6, 4], [7, 4], [8, 4], // Auxiliary Nodes -> WikiMind Hub
    ];

    let mouse = { x: -1000, y: -1000 };

    const handleMouseMove = (e) => {
      const rect = canvas.getBoundingClientRect();
      mouse.x = e.clientX - rect.left;
      mouse.y = e.clientY - rect.top;
    };

    const handleMouseLeave = () => {
      mouse = { x: -1000, y: -1000 };
    };

    canvas.addEventListener('mousemove', handleMouseMove);
    canvas.addEventListener('mouseleave', handleMouseLeave);

    const render = () => {
      ctx.clearRect(0, 0, width, height);

      // Node Physics Bounds Check
      initialNodes.forEach((node) => {
        node.x += node.vx;
        node.y += node.vy;

        if (node.x - node.r < 10 || node.x + node.r > width - 10) node.vx *= -1;
        if (node.y - node.r < 10 || node.y + node.r > height - 10) node.vy *= -1;

        const dx = mouse.x - node.x;
        const dy = mouse.y - node.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 100) {
          node.x += (dx / dist) * 0.4;
          node.y += (dy / dist) * 0.4;
        }
      });

      // 1. Draw Dotted Network Connecting Edges
      ctx.save();
      ctx.setLineDash([4, 4]);
      ctx.lineWidth = 1.5;
      ctx.strokeStyle = isLight ? 'rgba(37, 99, 235, 0.35)' : 'rgba(56, 189, 248, 0.35)';

      links.forEach(([i, j]) => {
        const n1 = initialNodes[i];
        const n2 = initialNodes[j];
        ctx.beginPath();
        ctx.moveTo(n1.x, n1.y);
        ctx.lineTo(n2.x, n2.y);
        ctx.stroke();
      });
      ctx.restore();

      // 2. Render Interactive Format Nodes & Badges
      initialNodes.forEach((node) => {
        const dx = mouse.x - node.x;
        const dy = mouse.y - node.y;
        const isHovered = Math.sqrt(dx * dx + dy * dy) < node.r;

        ctx.save();
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.r, 0, Math.PI * 2);

        // Custom Format Radial Gradient Fill
        const grad = ctx.createRadialGradient(
          node.x - node.r * 0.3,
          node.y - node.r * 0.3,
          2,
          node.x,
          node.y,
          node.r
        );

        const colors = node.gradient || ['#60A5FA', '#2563EB', '#1D4ED8'];
        grad.addColorStop(0, colors[0]);
        grad.addColorStop(0.6, colors[1]);
        grad.addColorStop(1, colors[2]);

        ctx.fillStyle = grad;
        ctx.fill();

        // Border Glow Stroke
        ctx.lineWidth = isHovered ? 4 : 2.5;
        ctx.strokeStyle = isHovered ? '#FFFFFF' : colors[0];
        ctx.shadowColor = colors[1];
        ctx.shadowBlur = isHovered ? 18 : 8;
        ctx.stroke();

        // Node Format Labels
        ctx.fillStyle = '#FFFFFF';
        ctx.textAlign = 'center';

        if (node.subtext) {
          ctx.font = `800 ${Math.min(node.r * 0.38, 12)}px Inter, sans-serif`;
          ctx.textBaseline = 'bottom';
          ctx.fillText(node.label, node.x, node.y + 1);

          ctx.font = `600 ${Math.min(node.r * 0.28, 9)}px Inter, sans-serif`;
          ctx.fillStyle = 'rgba(255, 255, 255, 0.85)';
          ctx.textBaseline = 'top';
          ctx.fillText(node.subtext, node.x, node.y + 3);
        } else {
          ctx.font = `700 ${Math.min(node.r * 0.42, 11)}px Inter, sans-serif`;
          ctx.textBaseline = 'middle';
          ctx.fillText(node.label, node.x, node.y);
        }

        ctx.restore();
      });

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    const handleClick = (e) => {
      const rect = canvas.getBoundingClientRect();
      const clickX = e.clientX - rect.left;
      const clickY = e.clientY - rect.top;

      initialNodes.forEach((node) => {
        const dx = clickX - node.x;
        const dy = clickY - node.y;
        if (Math.sqrt(dx * dx + dy * dy) < node.r) {
          if (onNodeClick) onNodeClick(node.label);
        }
      });
    };

    canvas.addEventListener('click', handleClick);

    return () => {
      window.removeEventListener('resize', handleResize);
      canvas.removeEventListener('mousemove', handleMouseMove);
      canvas.removeEventListener('mouseleave', handleMouseLeave);
      canvas.removeEventListener('click', handleClick);
      cancelAnimationFrame(animationFrameId);
    };
  }, [onNodeClick, isLight]);

  return (
    <div style={{ width: '100%', height: '360px', position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <canvas 
        ref={canvasRef} 
        style={{ width: '100%', height: '100%', cursor: 'pointer' }}
      />
    </div>
  );
}
