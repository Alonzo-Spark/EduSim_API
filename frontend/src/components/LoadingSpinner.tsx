import React from 'react';
import { motion } from 'framer-motion';

export const LoadingSpinner: React.FC = () => {
  return (
    <div className="flex flex-col items-center justify-center space-y-4 p-8">
      <div className="relative w-20 h-20">
        {/* Outer glowing ring */}
        <motion.div
          className="absolute inset-0 rounded-full border-4 border-t-physics-neonCyan border-r-physics-neonCyan border-b-transparent border-l-transparent"
          animate={{ rotate: 360 }}
          transition={{ repeat: Infinity, duration: 1.2, ease: "linear" }}
          style={{ filter: "drop-shadow(0 0 8px #00eeff)" }}
        />
        
        {/* Inner reverse-rotating ring */}
        <motion.div
          className="absolute inset-2 rounded-full border-4 border-t-transparent border-r-transparent border-b-physics-neonMagenta border-l-physics-neonMagenta"
          animate={{ rotate: -360 }}
          transition={{ repeat: Infinity, duration: 1.5, ease: "linear" }}
          style={{ filter: "drop-shadow(0 0 6px #f43f5e)" }}
        />
        
        {/* Center dot pulsing */}
        <motion.div
          className="absolute inset-7 rounded-full bg-physics-neonYellow"
          animate={{ scale: [0.8, 1.2, 0.8] }}
          transition={{ repeat: Infinity, duration: 2, ease: "easeInOut" }}
        />
      </div>
      <div className="flex flex-col items-center space-y-1">
        <motion.span 
          className="font-mono text-xs text-physics-neonCyan uppercase tracking-widest"
          animate={{ opacity: [0.4, 1, 0.4] }}
          transition={{ repeat: Infinity, duration: 1.5 }}
        >
          Compiling Vector Physics...
        </motion.span>
        <span className="font-mono text-[10px] text-slate-500">LLM Engine Pipeline Active</span>
      </div>
    </div>
  );
};

export default LoadingSpinner;
