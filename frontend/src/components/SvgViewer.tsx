import React, { useState } from 'react';
import { ZoomIn, ZoomOut, RotateCcw, Download, Sparkles, AlertTriangle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface SvgViewerProps {
  svgCode: string | null;
  prompt: string | null;
  filename: string | null;
  error: string | null;
  isLoading: boolean;
  onDownload: () => void;
}

export const SvgViewer: React.FC<SvgViewerProps> = ({
  svgCode,
  prompt,
  filename,
  error,
  isLoading,
  onDownload
}) => {
  const [scale, setScale] = useState(1);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  const handleZoomIn = () => setScale(prev => Math.min(prev + 0.15, 3));
  const handleZoomOut = () => setScale(prev => Math.max(prev - 0.15, 0.4));
  
  const handleReset = () => {
    setScale(1);
    setPosition({ x: 0, y: 0 });
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    if (!svgCode) return;
    setIsDragging(true);
    setDragStart({ x: e.clientX - position.x, y: e.clientY - position.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    setPosition({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y
    });
  };

  const handleMouseUp = () => setIsDragging(false);

  return (
    <div 
      className="glass-panel rounded-xl flex-1 flex flex-col relative overflow-hidden h-full shadow-2xl min-h-[500px] engineering-grid"
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      {/* Top blueprint bar */}
      <div className="absolute top-0 left-0 right-0 h-12 bg-slate-950/80 border-b border-physics-border flex items-center justify-between px-5 z-20">
        <div className="flex items-center space-x-2">
          <div className="w-2.5 h-2.5 rounded-full bg-physics-neonCyan animate-ping" />
          <span className="font-mono text-xs font-bold text-slate-300 tracking-widest uppercase">
            {prompt ? `SIMULATION CANVAS: ${prompt}` : 'PHYSICS SIMULATOR VIEWPORT'}
          </span>
        </div>

        {svgCode && (
          <div className="flex items-center space-x-2">
            <button
              onClick={handleZoomIn}
              title="Zoom In"
              className="p-1.5 rounded bg-slate-900 border border-physics-border hover:border-physics-neonCyan hover:text-physics-neonCyan text-slate-400 transition-all cursor-pointer"
            >
              <ZoomIn className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={handleZoomOut}
              title="Zoom Out"
              className="p-1.5 rounded bg-slate-900 border border-physics-border hover:border-physics-neonCyan hover:text-physics-neonCyan text-slate-400 transition-all cursor-pointer"
            >
              <ZoomOut className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={handleReset}
              title="Reset View"
              className="p-1.5 rounded bg-slate-900 border border-physics-border hover:border-physics-neonCyan hover:text-physics-neonCyan text-slate-400 transition-all cursor-pointer"
            >
              <RotateCcw className="w-3.5 h-3.5" />
            </button>
            <div className="w-[1px] h-4 bg-physics-border mx-1" />
            <button
              onClick={onDownload}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded bg-physics-neonYellow/10 border border-physics-neonYellow/30 hover:border-physics-neonYellow hover:bg-physics-neonYellow/20 text-physics-neonYellow transition-all font-mono text-[10px] font-bold cursor-pointer"
            >
              <Download className="w-3.5 h-3.5" />
              <span>SAVE SVG</span>
            </button>
          </div>
        )}
      </div>

      {/* Main Viewport Container */}
      <div 
        className={`flex-1 flex items-center justify-center relative overflow-hidden select-none ${
          svgCode ? 'cursor-grab active:cursor-grabbing' : ''
        }`}
        onMouseDown={handleMouseDown}
      >
        <AnimatePresence mode="wait">
          {error && (
            <motion.div 
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0 }}
              className="absolute glass-card p-6 rounded-lg max-w-md border border-physics-neonMagenta/40 flex flex-col items-center text-center space-y-3 z-10 mx-4"
            >
              <AlertTriangle className="w-10 h-10 text-physics-neonMagenta animate-bounce" />
              <h3 className="font-mono text-sm font-bold text-physics-neonMagenta uppercase tracking-wider">COMPILER SCHEMATIC ERROR</h3>
              <p className="text-xs text-slate-400 font-mono leading-relaxed">{error}</p>
            </motion.div>
          )}

          {!svgCode && !error && !isLoading && (
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="absolute flex flex-col items-center justify-center text-center space-y-4 max-w-sm z-10 px-4"
            >
              <div className="w-16 h-16 rounded-full bg-slate-950/60 border border-physics-border flex items-center justify-center glow-cyan-pulse">
                <Sparkles className="w-8 h-8 text-physics-neonCyan animate-pulse" />
              </div>
              <h3 className="font-mono text-xs font-bold text-slate-300 uppercase tracking-widest">Awaiting Simulation Parameters</h3>
              <p className="font-mono text-[10px] text-slate-500 leading-normal">
                Type a simulation query like "pendulum with gold bob" or "rotating gear system" and click the compile button to render.
              </p>
            </motion.div>
          )}
        </AnimatePresence>

        {/* The SVG Content Viewport Wrapper */}
        {svgCode && !isLoading && (
          <motion.div
            style={{
              transform: `translate(${position.x}px, ${position.y}px) scale(${scale})`,
              transformOrigin: 'center center',
              transition: isDragging ? 'none' : 'transform 0.15s ease-out'
            }}
            className="w-full h-full flex items-center justify-center p-8 mt-12"
            dangerouslySetInnerHTML={{ __html: svgCode }}
          />
        )}
      </div>

      {/* Blueprint grid coordinates footer overlay */}
      <div className="absolute bottom-3 left-4 font-mono text-[9px] text-slate-600 flex space-x-4 z-20 pointer-events-none">
        <span>X: {position.x}px</span>
        <span>Y: {position.y}px</span>
        <span>SCALE: {Math.round(scale * 100)}%</span>
        {filename && <span className="text-physics-neonCyan/50 font-bold uppercase truncate max-w-[200px]">FILE: {filename}</span>}
      </div>
    </div>
  );
};

export default SvgViewer;
