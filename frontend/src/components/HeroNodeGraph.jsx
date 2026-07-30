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

    // Preload WikiMind Logo for Central Hub Node
    const logoImg = new Image();
    let logoLoaded = false;
    logoImg.src = '/logo-color.png';
    logoImg.onload = () => {
      logoLoaded = true;
    };

    const handleResize = () => {
      if (canvas.parentElement) {
        width = canvas.width = canvas.parentElement.clientWidth;
        height = canvas.height = 360;
      }
    };
    window.addEventListener('resize', handleResize);

    // Central WikiMind Logo Hub + Entity Type Nodes
    const initialNodes = [
      // Central WikiMind Hub (Index 0)
      { x: width * 0.50, y: height * 0.48, r: 44, vx: 0.08, vy: -0.08, label: 'WikiMind', subtext: 'HUB', format: 'hub', gradient: ['#FFFFFF', '#FFFFFF', '#F8FAFC'] },

      // 6 Core Knowledge Graph Entity Types (Surrounding Hub)
      { x: width * 0.20, y: height * 0.25, r: 32, vx: 0.2, vy: 0.15, label: 'ORGANIZATION', subtext: 'COMPANY', format: 'entity', gradient: ['#60A5FA', '#2563EB', '#1D4ED8'] },
      { x: width * 0.80, y: height * 0.25, r: 32, vx: -0.2, vy: 0.15, label: 'PERSON', subtext: 'AUTHOR', format: 'entity', gradient: ['#F87171', '#EF4444', '#DC2626'] },
      { x: width * 0.15, y: height * 0.65, r: 32, vx: 0.15, vy: -0.2, label: 'CONCEPT', subtext: 'TOPIC', format: 'entity', gradient: ['#34D399', '#10B981', '#047857'] },
      { x: width * 0.85, y: height * 0.65, r: 32, vx: -0.15, vy: -0.2, label: 'TECHNOLOGY', subtext: 'TOOL', format: 'entity', gradient: ['#A78BFA', '#8B5CF6', '#6D28D9'] },
      { x: width * 0.50, y: height * 0.15, r: 28, vx: -0.1, vy: 0.1, label: 'LOCATION', subtext: 'PLACE', format: 'entity', gradient: ['#FBBF24', '#F59E0B', '#D97706'] },
      { x: width * 0.50, y: height * 0.85, r: 28, vx: 0.1, vy: -0.1, label: 'EVENT', subtext: 'DATE', format: 'entity', gradient: ['#38BDF8', '#0EA5E9', '#0284C7'] },
    ];

    // Connections linking all Entity Nodes to central WikiMind Hub & interconnects
    const links = [
      [1, 0], [2, 0], [3, 0], [4, 0], [5, 0], [6, 0], // Entity Nodes -> WikiMind Hub
      [1, 5], [2, 5],                                 // ORGANIZATION & PERSON -> LOCATION
      [3, 6], [4, 6],                                 // CONCEPT & TECHNOLOGY -> EVENT
      [1, 3], [2, 4],                                 // Cross-entity connections
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
        ctx.strokeStyle = node.format === 'hub' ? '#2563EB' : (isHovered ? '#FFFFFF' : colors[0]);
        ctx.shadowColor = node.format === 'hub' ? 'rgba(37, 99, 235, 0.4)' : colors[1];
        ctx.shadowBlur = isHovered ? 18 : 10;
        ctx.stroke();

        // Central Hub: Draw WikiMind Logo Image Inside Circle
        if (node.format === 'hub' && logoLoaded) {
          const size = node.r * 1.5;
          ctx.save();
          ctx.beginPath();
          ctx.arc(node.x, node.y, node.r * 0.85, 0, Math.PI * 2);
          ctx.clip();
          ctx.drawImage(logoImg, node.x - size / 2, node.y - size / 2, size, size);
          ctx.restore();
        } else {
          // Node Format Labels
          ctx.fillStyle = node.format === 'hub' ? '#09090B' : '#FFFFFF';
          ctx.textAlign = 'center';

          if (node.subtext) {
            ctx.font = `800 ${Math.min(node.r * 0.38, 12)}px Inter, sans-serif`;
            ctx.textBaseline = 'bottom';
            ctx.fillText(node.label, node.x, node.y + 1);

            ctx.font = `600 ${Math.min(node.r * 0.28, 9)}px Inter, sans-serif`;
            ctx.fillStyle = node.format === 'hub' ? '#64748B' : 'rgba(255, 255, 255, 0.85)';
            ctx.textBaseline = 'top';
            ctx.fillText(node.subtext, node.x, node.y + 3);
          } else {
            ctx.font = `700 ${Math.min(node.r * 0.42, 11)}px Inter, sans-serif`;
            ctx.textBaseline = 'middle';
            ctx.fillText(node.label, node.x, node.y);
          }
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

    return () => {
      window.removeEventListener('resize', handleResize);
      canvas.removeEventListener('mousemove', handleMouseMove);
      canvas.removeEventListener('mouseleave', handleMouseLeave);
      cancelAnimationFrame(animationFrameId);
    };
  }, [onNodeClick, isLight]);

  return (
    <div style={{ width: '100%', height: '360px', position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <canvas 
        ref={canvasRef} 
        style={{ width: '100%', height: '100%' }}
      />
    </div>
  );
}
