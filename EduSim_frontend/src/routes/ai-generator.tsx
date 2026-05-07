/**
 * AI Generator Page Route
 * Main page for AI-powered simulation generation
 */

import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { SimulationConfig } from "@/types/simulation";
import { AIInputPanel } from "@/components/AIInputPanel";
import { SimulationCanvas } from "@/components/SimulationCanvas";

export const Route = createFileRoute("/ai-generator")({
  component: AIGeneratorPage,
});

function AIGeneratorPage() {
  const [simulationConfig, setSimulationConfig] = useState<SimulationConfig | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSimulationGenerated = (config: any) => {
    setSimulationConfig(config);
    setError(null);
  };

  return (
    <div className="h-screen w-full bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-white overflow-hidden">
      {/* Main Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 h-full gap-6 p-6">
        {/* Left: Input Panel */}
        <div className="min-w-0">
          <AIInputPanel onSimulationGenerated={handleSimulationGenerated} className="h-full" />
        </div>

        {/* Right: Simulation Canvas */}
        <div className="min-w-0">
          <SimulationCanvas config={simulationConfig} className="h-full" onError={setError} />
        </div>
      </div>

      {/* Global Error Toast */}
      {error && (
        <div className="fixed bottom-6 right-6 bg-red-500/10 border border-red-500/30 rounded-lg p-4 max-w-md">
          <p className="text-sm text-red-300">{error}</p>
        </div>
      )}
    </div>
  );
}
