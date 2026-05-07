/**
 * AI Input Panel Component
 * Handles user input for simulation generation
 */

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card } from "@/components/ui/card";
import { LoadingSpinner } from "@/components/LoadingSpinner";
import { AlertCircle, Sparkles, History, X } from "lucide-react";
import { useSimulationGenerator } from "@/hooks/useSimulationGenerator";
import { cn } from "@/lib/utils";

interface AIInputPanelProps {
  onSimulationGenerated?: (config: any) => void;
  className?: string;
}

const EXAMPLE_PROMPTS = [
  "Create a solar system with a sun and 3 planets orbiting",
  "Show 3 red balls bouncing with low gravity",
  "Create a pendulum on the moon",
  "Simulate projectile motion with initial velocity 20m/s at 45 degrees",
  "Show a spring-mass system oscillating",
  "Create a wave in water",
];

const PROMPT_PLACEHOLDERS = [
  "Describe a ball bouncing...",
  "Create a planet orbiting...",
  "Show a pendulum swinging...",
  "Simulate projectile motion...",
];

export function AIInputPanel({ onSimulationGenerated, className }: AIInputPanelProps) {
  const [prompt, setPrompt] = useState("");
  const [history, setHistory] = useState<string[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const [placeholder, setPlaceholder] = useState(PROMPT_PLACEHOLDERS[0]);

  const { config, loading, error, generate, reasoning } = useSimulationGenerator();

  // Cycle through placeholders
  useEffect(() => {
    const interval = setInterval(() => {
      setPlaceholder((prev) => {
        const currentIndex = PROMPT_PLACEHOLDERS.indexOf(prev);
        const nextIndex = (currentIndex + 1) % PROMPT_PLACEHOLDERS.length;
        return PROMPT_PLACEHOLDERS[nextIndex];
      });
    }, 4000);
    return () => clearInterval(interval);
  }, []);

  // Load history from localStorage
  useEffect(() => {
    const saved = localStorage.getItem("simulation-prompt-history");
    if (saved) {
      try {
        setHistory(JSON.parse(saved));
      } catch {
        // Ignore parsing errors
      }
    }
  }, []);

  // Save history to localStorage
  useEffect(() => {
    if (history.length > 0) {
      localStorage.setItem("simulation-prompt-history", JSON.stringify(history.slice(0, 10)));
    }
  }, [history]);

  // Handle simulation generation
  useEffect(() => {
    if (config && onSimulationGenerated) {
      onSimulationGenerated(config);
    }
  }, [config, onSimulationGenerated]);

  const handleGenerate = async () => {
    if (!prompt.trim()) return;

    // Add to history
    if (!history.includes(prompt)) {
      setHistory((prev) => [prompt, ...prev.slice(0, 9)]);
    }

    await generate(prompt);
  };

  const handleQuickPrompt = (quickPrompt: string) => {
    setPrompt(quickPrompt);
    setShowHistory(false);
  };

  const clearHistory = () => {
    setHistory([]);
    localStorage.removeItem("simulation-prompt-history");
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      handleGenerate();
    }
  };

  return (
    <div className={cn("h-full flex flex-col", className)}>
      <Card className="flex-1 flex flex-col bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 border-purple-500/20 shadow-xl">
        {/* Header */}
        <div className="p-6 border-b border-purple-500/20">
          <div className="flex items-center gap-2 mb-2">
            <Sparkles className="w-5 h-5 text-purple-400" />
            <h2 className="text-xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
              AI Simulation Generator
            </h2>
          </div>
          <p className="text-sm text-slate-400">
            Describe any physics or educational simulation in natural language
          </p>
        </div>

        {/* Main Content */}
        <div className="flex-1 flex flex-col p-6 gap-4 overflow-hidden">
          {/* Input Area */}
          <div className="flex flex-col gap-2">
            <label className="text-sm font-medium text-slate-300">Your Prompt</label>
            <div className="relative">
              <Textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={placeholder}
                className="min-h-24 bg-slate-800/50 border-purple-500/30 focus:border-purple-400 text-white resize-none"
                disabled={loading}
              />
              {prompt && (
                <button
                  onClick={() => setPrompt("")}
                  className="absolute top-2 right-2 p-1 hover:bg-slate-700 rounded"
                  aria-label="Clear prompt"
                >
                  <X className="w-4 h-4 text-slate-400" />
                </button>
              )}
            </div>
          </div>

          {/* Error Display */}
          {error && (
            <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-300">{error}</p>
            </div>
          )}

          {/* Reasoning Display */}
          {reasoning && (
            <div className="p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg text-sm text-blue-300">
              <p className="font-medium mb-1">AI Reasoning:</p>
              <p className="text-xs">{reasoning}</p>
            </div>
          )}

          {/* Quick Buttons */}
          <div className="grid grid-cols-2 gap-2">
            <Button
              onClick={handleGenerate}
              disabled={!prompt.trim() || loading}
              className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white font-medium"
            >
              {loading ? (
                <>
                  <LoadingSpinner className="w-4 h-4 mr-2" />
                  Generating...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 mr-2" />
                  Generate
                </>
              )}
            </Button>

            <Button
              onClick={() => setShowHistory(!showHistory)}
              variant="outline"
              className="border-purple-500/30 hover:bg-purple-500/10"
              disabled={history.length === 0}
            >
              <History className="w-4 h-4 mr-2" />
              History
            </Button>
          </div>

          {/* History Dropdown */}
          {showHistory && history.length > 0 && (
            <div className="border border-purple-500/30 rounded-lg bg-slate-800/50 overflow-hidden">
              <div className="max-h-32 overflow-y-auto">
                {history.map((item, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleQuickPrompt(item)}
                    className="w-full text-left p-2 hover:bg-purple-500/20 border-b border-purple-500/10 text-sm text-slate-300 transition-colors last:border-b-0"
                  >
                    {item.substring(0, 50)}...
                  </button>
                ))}
              </div>
              {history.length > 0 && (
                <button
                  onClick={clearHistory}
                  className="w-full p-2 text-xs text-slate-400 hover:text-red-400 border-t border-purple-500/10"
                >
                  Clear History
                </button>
              )}
            </div>
          )}

          {/* Example Prompts */}
          <div className="border-t border-purple-500/20 pt-4">
            <p className="text-xs font-medium text-slate-400 mb-2">Quick Examples:</p>
            <div className="grid grid-cols-1 gap-2">
              {EXAMPLE_PROMPTS.slice(0, 3).map((example, idx) => (
                <button
                  key={idx}
                  onClick={() => handleQuickPrompt(example)}
                  className="text-left p-2 text-xs bg-purple-500/5 hover:bg-purple-500/15 border border-purple-500/20 rounded text-slate-300 transition-colors"
                >
                  {example}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Footer Help */}
        <div className="border-t border-purple-500/20 p-4 text-xs text-slate-500">
          <p>
            💡 Tip: Use specific values like gravity, velocities, and object types for better
            results
          </p>
        </div>
      </Card>
    </div>
  );
}
