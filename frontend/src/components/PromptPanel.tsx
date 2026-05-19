import React, { useState } from 'react';
import { Sparkles, Terminal } from 'lucide-react';
import { motion } from 'framer-motion';

interface PromptPanelProps {
  onSubmit: (prompt: string) => void;
  isLoading: boolean;
}

export const PromptPanel: React.FC<PromptPanelProps> = ({ onSubmit, isLoading }) => {
  const [prompt, setPrompt] = useState('');
  
  const placeholders = [
    "pendulum with gold bob",
    "gear system with 3 rotating gears",
    "gold blob connected to spring",
    "pulley system with mechanical weight",
    "car collision simulation with momentum vectors"
  ];

  const handleQuickPrompt = (p: string) => {
    if (isLoading) return;
    setPrompt(p);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim() || isLoading) return;
    onSubmit(prompt.trim());
  };

  return (
    <div className="glass-panel rounded-xl p-5 space-y-4 flex flex-col relative overflow-hidden shadow-2xl">
      {/* Laser Top Line decoration */}
      <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-physics-neonCyan via-physics-neonMagenta to-physics-neonYellow" />
      
      <div className="flex items-center space-x-2">
        <Terminal className="w-5 h-5 text-physics-neonCyan" />
        <h2 className="font-mono text-sm font-bold text-slate-200 tracking-wider">INPUT SCHEMATIC PROMPT</h2>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="relative">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Describe the scientific object or simulation you want..."
            disabled={isLoading}
            maxLength={250}
            className="w-full h-36 bg-slate-950/80 border border-physics-border rounded-lg p-3 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-physics-neonCyan focus:border-physics-neonCyan transition-all disabled:opacity-50 disabled:cursor-not-allowed resize-none font-mono"
          />
          <div className="absolute bottom-2 right-3 font-mono text-[10px] text-slate-600">
            {prompt.length}/250
          </div>
        </div>

        {/* Action Button */}
        <motion.button
          type="submit"
          disabled={!prompt.trim() || isLoading}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className="w-full bg-gradient-to-r from-physics-neonCyan via-[#0ea5e9] to-[#0284c7] hover:from-physics-neonCyan hover:to-[#0284c7] text-slate-950 font-bold py-3 px-4 rounded-lg flex items-center justify-center space-x-2 transition-all shadow-[0_0_15px_rgba(0,238,255,0.2)] disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none"
        >
          <Sparkles className="w-4 h-4 text-slate-950 animate-pulse" />
          <span className="font-mono tracking-wider text-xs uppercase">Compile AI Physics SVG</span>
        </motion.button>
      </form>

      {/* Suggested Prompt tags */}
      <div className="space-y-2">
        <div className="font-mono text-[10px] text-slate-500 uppercase tracking-widest">Quick Suggestion Presets:</div>
        <div className="flex flex-wrap gap-2">
          {placeholders.map((preset, idx) => (
            <motion.button
              key={idx}
              onClick={() => handleQuickPrompt(preset)}
              disabled={isLoading}
              whileHover={{ scale: 1.05 }}
              className="text-[10px] font-mono bg-slate-950/50 hover:bg-slate-900 border border-physics-border hover:border-physics-neonCyan text-slate-400 hover:text-physics-neonCyan px-2.5 py-1.5 rounded-md transition-all cursor-pointer"
            >
              + {preset}
            </motion.button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default PromptPanel;
