import { useState, useEffect } from 'react';
import { Activity, Layers, Cpu } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import PromptPanel from './components/PromptPanel';
import HistoryPanel from './components/HistoryPanel';
import SvgViewer from './components/SvgViewer';
import LoadingSpinner from './components/LoadingSpinner';
import InteractiveSimulation from './components/InteractiveSimulation';
import { generateSVG, getSVGHistory, SVGHistoryItem, generateSimulationDSL, SimulationDSL } from './services/api';

function App() {
  const [svgCode, setSvgCode] = useState<string | null>(null);
  const [simulationDSL, setSimulationDSL] = useState<SimulationDSL | null>(null);
  const [currentPrompt, setCurrentPrompt] = useState<string | null>(null);
  const [currentFilename, setCurrentFilename] = useState<string | null>(null);
  
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<SVGHistoryItem[]>([]);
  const [currentTab, setCurrentTab] = useState<'design' | 'simulation'>('simulation');

  // Load history on mount
  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    try {
      const data = await getSVGHistory();
      setHistory(data);
    } catch (err) {
      console.error("Failed to load history:", err);
    }
  };

  const handleGenerate = async (prompt: string) => {
    setIsLoading(true);
    setError(null);
    setSvgCode(null);
    setSimulationDSL(null);
    setCurrentPrompt(prompt);
    
    try {
      // Trigger SVG generation and Simulation DSL compilation in parallel
      const [svgResponse, dslResponse] = await Promise.all([
        generateSVG(prompt),
        generateSimulationDSL(prompt).catch((err) => {
          console.warn("DSL synthesis error, running in Design mode fallback:", err);
          return null;
        })
      ]);

      if (svgResponse.success) {
        setSvgCode(svgResponse.svg_code);
        setCurrentFilename(svgResponse.filename);
        await loadHistory();
      } else {
        setError(svgResponse.message || "An unexpected compile error occurred.");
      }

      if (dslResponse && dslResponse.success) {
        setSimulationDSL(dslResponse.dsl);
        setCurrentTab('simulation'); // Default to Interactive Physics Mode
      } else {
        setCurrentTab('design');
      }
    } catch (err: any) {
      console.error("Simulation generation error:", err);
      setError(
        err.response?.data?.detail || 
        "Failed to reach the AI physics compiler. Verify the backend is active."
      );
      setCurrentTab('design');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectHistoryItem = async (item: SVGHistoryItem) => {
    setIsLoading(true);
    setError(null);
    setCurrentPrompt(item.prompt);
    setCurrentFilename(item.filename);
    setSimulationDSL(null);

    // Fetch the raw SVG content from the static file path
    const backendUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    
    try {
      const res = await fetch(`${backendUrl}${item.file_path}`);
      if (!res.ok) throw new Error("Failed to load SVG content");
      const text = await res.text();
      setSvgCode(text);

      // Attempt to load dynamic DSL for this history item prompt
      const dslResponse = await generateSimulationDSL(item.prompt).catch(() => null);
      if (dslResponse && dslResponse.success) {
        setSimulationDSL(dslResponse.dsl);
        setCurrentTab('simulation');
      } else {
        setCurrentTab('design');
      }
    } catch (err) {
      console.error(err);
      setError("Failed to retrieve the historical vector file.");
      setCurrentTab('design');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownload = () => {
    if (!svgCode || !currentPrompt) return;
    
    const blob = new Blob([svgCode], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    
    const slug = currentPrompt.toLowerCase().replace(/[^a-z0-9]+/g, '_').trim();
    link.href = url;
    link.download = `edusim_${slug || 'simulation'}.svg`;
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="w-screen h-screen flex flex-col bg-[#05080f] overflow-hidden select-none font-sans">
      
      {/* Top Banner Navigation */}
      <header className="h-16 border-b border-physics-border bg-slate-950/80 px-6 flex items-center justify-between z-30 shrink-0">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-physics-neonCyan to-physics-neonMagenta flex items-center justify-center shadow-lg">
            <Cpu className="w-4 h-4 text-slate-950" />
          </div>
          <div className="flex flex-col">
            <span className="font-mono text-xs font-bold text-slate-100 uppercase tracking-widest leading-none">
              EduSim AI
            </span>
            <span className="font-mono text-[9px] text-physics-neonCyan tracking-wider mt-1 font-bold">
              VECTOR SCHEMATIC COMPILER
            </span>
          </div>
        </div>

        {/* Telemetry Indicators */}
        <div className="flex items-center space-x-6 text-[10px] font-mono text-slate-500">
          <div className="flex items-center space-x-1.5">
            <Activity className="w-3 h-3 text-physics-neonGreen animate-pulse" />
            <span>AI CORE: ACTIVE</span>
          </div>
          <div className="flex items-center space-x-1.5">
            <Layers className="w-3 h-3 text-physics-neonCyan" />
            <span>RENDER PIPELINE: H11</span>
          </div>
        </div>
      </header>

      {/* Main Workspace split */}
      <main className="flex-1 flex overflow-hidden p-4 gap-4 relative">
        
        {/* Left side panel area */}
        <section className="w-80 flex flex-col gap-4 shrink-0 overflow-y-auto pr-1">
          <PromptPanel onSubmit={handleGenerate} isLoading={isLoading} />
          <HistoryPanel 
            history={history} 
            onSelect={handleSelectHistoryItem} 
            selectedFilename={currentFilename}
          />
        </section>

        {/* Right side display area */}
        <section className="flex-1 h-full flex flex-col relative overflow-hidden">
          <AnimatePresence mode="wait">
            {isLoading ? (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="absolute inset-0 z-20 flex items-center justify-center glass-panel rounded-xl"
              >
                <LoadingSpinner />
              </motion.div>
            ) : null}
          </AnimatePresence>

          {/* Premium Dual-Tab Selector */}
          {svgCode && (
            <div className="flex space-x-1 p-1 bg-slate-950/80 border border-physics-border rounded-lg mb-4 self-start font-mono text-[11px] font-bold z-10">
              <button
                onClick={() => setCurrentTab('simulation')}
                disabled={!simulationDSL}
                className={`px-4 py-2 rounded-md transition-all flex items-center space-x-2 cursor-pointer ${
                  currentTab === 'simulation'
                    ? 'bg-physics-neonCyan text-slate-950 shadow-[0_0_12px_rgba(0,238,255,0.4)]'
                    : 'text-slate-400 hover:text-slate-100 disabled:opacity-30 disabled:cursor-not-allowed'
                }`}
              >
                <Activity className="w-3.5 h-3.5" />
                <span>🔬 INTERACTIVE PHYSICS SIMULATION</span>
              </button>
              <button
                onClick={() => setCurrentTab('design')}
                className={`px-4 py-2 rounded-md transition-all flex items-center space-x-2 cursor-pointer ${
                  currentTab === 'design'
                    ? 'bg-physics-neonCyan text-slate-950 shadow-[0_0_12px_rgba(0,238,255,0.4)]'
                    : 'text-slate-400 hover:text-slate-100'
                }`}
              >
                <Layers className="w-3.5 h-3.5" />
                <span>🎨 HIGH-FIDELITY BLUEPRINT GRAPHIC</span>
              </button>
            </div>
          )}

          {/* Render Tab Workspace */}
          <div className="flex-1 h-full overflow-hidden flex flex-col">
            {currentTab === 'simulation' && simulationDSL ? (
              <InteractiveSimulation dsl={simulationDSL} prompt={currentPrompt || ''} />
            ) : (
              <SvgViewer
                svgCode={svgCode}
                prompt={currentPrompt}
                filename={currentFilename}
                error={error}
                isLoading={isLoading}
                onDownload={handleDownload}
              />
            )}
          </div>
        </section>

      </main>

    </div>
  );
}

export default App;

