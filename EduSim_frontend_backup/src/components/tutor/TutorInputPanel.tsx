import React, { useState } from "react";
import { Search, Send, Sparkles } from "lucide-react";

interface TutorInputPanelProps {
  onAnalyze: (query: string) => void;
  isLoading: boolean;
  className?: string;
}

const EXAMPLES = [
  "Explain force and acceleration",
  "What is momentum?",
  "Explain total internal reflection",
  "Difference between pitch and loudness",
  "Give formulas related to velocity",
];

export function TutorInputPanel({ onAnalyze, isLoading, className = "" }: TutorInputPanelProps) {
  const [query, setQuery] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onAnalyze(query);
    }
  };

  return (
    <div className={`glass-strong rounded-3xl p-8 flex flex-col gap-8 ${className}`}>
      <div className="flex items-center gap-4">
        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-[var(--neon-purple)] to-[var(--neon-blue)] flex items-center justify-center glow-purple">
          <Sparkles className="w-6 h-6 text-white" />
        </div>
        <div>
          <h2 className="text-2xl font-bold text-gradient">Physics Tutor</h2>
          <p className="text-sm text-muted-foreground">Ask me anything about physics concepts or formulas.</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="relative">
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Type your question here..."
          className="w-full h-40 bg-white/5 border border-white/10 rounded-2xl p-4 pr-14 text-lg focus:outline-none focus:ring-2 focus:ring-[var(--neon-purple)]/50 transition-all resize-none"
        />
        <button
          type="submit"
          disabled={isLoading || !query.trim()}
          className="absolute bottom-4 right-4 w-10 h-10 rounded-xl bg-gradient-to-r from-[var(--neon-purple)] to-[var(--neon-blue)] flex items-center justify-center text-white shadow-lg disabled:opacity-50 disabled:cursor-not-allowed hover:scale-105 active:scale-95 transition-all glow-purple"
        >
          <Send className="w-5 h-5" />
        </button>
      </form>

      <div className="flex flex-col gap-4">
        <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Example Prompts</h3>
        <div className="flex flex-wrap gap-2">
          {EXAMPLES.map((ex) => (
            <button
              key={ex}
              onClick={() => {
                setQuery(ex);
                onAnalyze(ex);
              }}
              disabled={isLoading}
              className="px-4 py-2 rounded-xl bg-white/5 border border-white/10 text-sm hover:bg-white/10 hover:border-white/20 transition-all text-left"
            >
              {ex}
            </button>
          ))}
        </div>
      </div>
      
      <button
        onClick={handleSubmit}
        disabled={isLoading || !query.trim()}
        className="w-full py-4 rounded-2xl bg-gradient-to-r from-[var(--neon-purple)] to-[var(--neon-blue)] font-bold text-lg shadow-xl hover:glow-purple transition-all flex items-center justify-center gap-3"
      >
        {isLoading ? (
          <div className="w-6 h-6 border-2 border-white/30 border-t-white rounded-full animate-spin" />
        ) : (
          <>
            <Search className="w-5 h-5" />
            Analyze Question
          </>
        )}
      </button>
    </div>
  );
}
