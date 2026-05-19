import React from 'react';
import { History, Download, Eye, FileJson } from 'lucide-react';
import { motion } from 'framer-motion';
import { SVGHistoryItem, getFullSvgUrl } from '../services/api';

interface HistoryPanelProps {
  history: SVGHistoryItem[];
  onSelect: (item: SVGHistoryItem) => void;
  selectedFilename: string | null;
}

export const HistoryPanel: React.FC<HistoryPanelProps> = ({ 
  history, 
  onSelect, 
  selectedFilename
}) => {
  return (
    <div className="glass-panel rounded-xl p-5 flex flex-col flex-1 relative overflow-hidden min-h-[300px] shadow-2xl">
      
      <div className="flex items-center justify-between pb-3 border-b border-physics-border">
        <div className="flex items-center space-x-2">
          <History className="w-5 h-5 text-physics-neonMagenta" />
          <h2 className="font-mono text-sm font-bold text-slate-200 tracking-wider">SCHEMATIC COMPILER HISTORY</h2>
        </div>
        <span className="font-mono text-[10px] bg-slate-900 border border-physics-border px-2 py-0.5 rounded text-physics-neonMagenta">
          {history.length} Saved
        </span>
      </div>

      <div className="overflow-y-auto flex-1 mt-4 space-y-2 pr-1 max-h-[380px]">
        {history.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-48 text-center text-slate-600 font-mono text-xs">
            <FileJson className="w-8 h-8 text-slate-700 mb-2 animate-pulse" />
            No compiled vectors yet.
            <br />
            Create one above!
          </div>
        ) : (
          history.map((item, idx) => {
            const isSelected = selectedFilename === item.filename;
            return (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.05 }}
                className={`glass-card p-3 rounded-lg flex items-center justify-between border transition-all relative group ${
                  isSelected 
                    ? 'border-physics-neonCyan bg-physics-neonCyan/5 shadow-[0_0_10px_rgba(0,238,255,0.15)]' 
                    : 'border-physics-border hover:border-slate-700 hover:bg-slate-950/40'
                }`}
              >
                <div 
                  onClick={() => onSelect(item)}
                  className="flex-1 cursor-pointer pr-2"
                >
                  <div className={`font-mono text-xs font-semibold truncate ${
                    isSelected ? 'text-physics-neonCyan' : 'text-slate-300'
                  }`}>
                    {item.prompt}
                  </div>
                  <div className="font-mono text-[9px] text-slate-500 mt-1 flex justify-between">
                    <span>{item.created_at}</span>
                  </div>
                </div>

                <div className="flex items-center space-x-1 opacity-60 group-hover:opacity-100 transition-opacity">
                  {/* Preview Indicator button */}
                  <button
                    onClick={() => onSelect(item)}
                    title="Load simulation in viewport"
                    className="p-1 rounded bg-slate-950/60 hover:bg-slate-900 border border-physics-border hover:border-physics-neonCyan text-slate-400 hover:text-physics-neonCyan cursor-pointer transition-all"
                  >
                    <Eye className="w-3.5 h-3.5" />
                  </button>

                  {/* Direct Download Button */}
                  <a
                    href={getFullSvgUrl(item.file_path)}
                    download={item.filename}
                    title="Download SVG file"
                    onClick={(e) => {
                      // Allow standard download through <a> link
                      e.stopPropagation();
                    }}
                    className="p-1 rounded bg-slate-950/60 hover:bg-slate-900 border border-physics-border hover:border-physics-neonYellow text-slate-400 hover:text-physics-neonYellow cursor-pointer transition-all"
                  >
                    <Download className="w-3.5 h-3.5" />
                  </a>
                </div>
              </motion.div>
            );
          })
        )}
      </div>
    </div>
  );
};

export default HistoryPanel;
