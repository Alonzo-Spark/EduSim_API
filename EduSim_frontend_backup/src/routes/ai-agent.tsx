import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { PageWrapper } from "@/components/Card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Sparkles,
  PlayCircle,
  Link2,
  Download,
  BookOpen,
  Lightbulb,
  Settings2,
  Cpu,
  Zap,
  Box,
  GitBranch,
  BarChart2,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { useAgentSimulation } from "@/hooks/useAgentSimulation";
import type { PhysicsDSL, DSLEntity, DSLInteraction, DSLVisualization } from "@/services/agentSimulationService";

export const Route = createFileRoute("/ai-agent")({
  component: AIAgentPage,
});

const EXAMPLE_PROMPTS = [
  {
    title: "Projectile Motion",
    prompt: "Create a projectile motion simulation showing trajectory with adjustable angle and velocity",
  },
  {
    title: "Newton's Second Law",
    prompt: "Visualize Newton's Second Law with a block on a surface and adjustable force",
  },
  {
    title: "Pendulum Oscillation",
    prompt: "Generate an interactive pendulum experiment with variable length and mass",
  },
  {
    title: "Momentum Conservation",
    prompt: "Simulate momentum conservation in elastic and inelastic collisions",
  },
];

const DSL_STAGES = [
  "Analyzing",
  "Detecting",
  "Retrieving",
  "Extracting",
  "Synthesizing",
  "Sanitizing",
  "Validating",
  "Saving",
  "Rendering",
];

// =========================================================
// Sub-components
// =========================================================

function ProgressBar({ percentage, stage }: { percentage: number; stage: string | null }) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-xs">
        <span className="text-muted-foreground">{stage || "Ready"}</span>
        <span className="font-semibold text-[var(--neon-cyan)]">{percentage}%</span>
      </div>
      <div className="w-full h-2 bg-slate-900/50 rounded-full overflow-hidden border border-white/10">
        <div
          className="h-full bg-gradient-to-r from-[var(--neon-purple)] to-[var(--neon-cyan)] transition-all duration-300"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}

function StageIndicator({ stages, currentStage }: { stages: string[]; currentStage: string | null }) {
  return (
    <div className="space-y-2">
      <p className="text-xs text-muted-foreground">Generation Pipeline</p>
      <div className="flex flex-wrap gap-1">
        {stages.map((stage) => {
          const isActive = currentStage?.toLowerCase().includes(stage.toLowerCase());
          return (
            <div
              key={stage}
              className={`px-2 py-1 rounded-full text-xs transition-colors whitespace-nowrap ${
                isActive
                  ? "bg-[var(--neon-cyan)] text-black font-semibold"
                  : "bg-slate-900/50 text-muted-foreground border border-white/10"
              }`}
            >
              {stage}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// DSL Panel sub-sections
function EntityCard({ entity }: { entity: DSLEntity }) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/5 p-3 space-y-1">
      <div className="flex items-center gap-2">
        <Box className="w-3.5 h-3.5 text-[var(--neon-cyan)]" />
        <span className="font-mono text-xs font-semibold text-white">{entity.id}</span>
        <span className="px-1.5 py-0.5 rounded bg-[var(--neon-purple)]/30 text-[10px] text-[var(--neon-purple)]">{entity.type}</span>
      </div>
      {entity.mass !== null && (
        <p className="text-xs text-muted-foreground">mass: {entity.mass} kg</p>
      )}
    </div>
  );
}

function InteractionCard({ interaction }: { interaction: DSLInteraction }) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/5 p-3 space-y-1">
      <div className="flex items-center gap-2">
        <GitBranch className="w-3.5 h-3.5 text-[var(--neon-purple)]" />
        <span className="font-mono text-xs font-semibold text-white">{interaction.type}</span>
        <span className="text-xs text-muted-foreground">→ {interaction.target}</span>
      </div>
      {Object.keys(interaction.parameters).length > 0 && (
        <pre className="text-[10px] text-muted-foreground/70 font-mono">
          {JSON.stringify(interaction.parameters, null, 2)}
        </pre>
      )}
    </div>
  );
}

function VisualizationBadge({ viz }: { viz: DSLVisualization }) {
  return (
    <span className="px-2 py-1 rounded-full bg-[var(--neon-cyan)]/10 border border-[var(--neon-cyan)]/30 text-[var(--neon-cyan)] text-xs font-mono">
      {viz.type}
    </span>
  );
}

function DSLInspector({ dsl }: { dsl: PhysicsDSL }) {
  const [showRaw, setShowRaw] = useState(false);

  return (
    <div className="space-y-4">
      {/* Header row */}
      <div className="flex items-center gap-3">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <Cpu className="w-4 h-4 text-[var(--neon-cyan)]" />
            <span className="text-sm font-semibold text-white font-mono">{dsl.simulation_type}</span>
          </div>
          <p className="text-xs text-muted-foreground mt-0.5">{dsl.topic}</p>
        </div>
        <div className="text-right text-xs text-muted-foreground space-y-0.5">
          <p>g = {dsl.environment.gravity} m/s²</p>
          <p>μ = {dsl.environment.friction}</p>
        </div>
      </div>

      {/* Entities */}
      <div>
        <p className="text-xs text-muted-foreground mb-2 flex items-center gap-1.5">
          <Box className="w-3.5 h-3.5" /> Entities ({dsl.entities.length})
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {dsl.entities.map((e) => <EntityCard key={e.id} entity={e} />)}
        </div>
      </div>

      {/* Interactions */}
      <div>
        <p className="text-xs text-muted-foreground mb-2 flex items-center gap-1.5">
          <GitBranch className="w-3.5 h-3.5" /> Interactions ({dsl.interactions.length})
        </p>
        <div className="space-y-2">
          {dsl.interactions.map((inter, i) => <InteractionCard key={i} interaction={inter} />)}
        </div>
      </div>

      {/* Visualizations */}
      <div>
        <p className="text-xs text-muted-foreground mb-2 flex items-center gap-1.5">
          <BarChart2 className="w-3.5 h-3.5" /> Visualizations
        </p>
        <div className="flex flex-wrap gap-2">
          {dsl.visualizations.map((v, i) => <VisualizationBadge key={i} viz={v} />)}
        </div>
      </div>

      {/* Equations */}
      {dsl.equations.length > 0 && (
        <div>
          <p className="text-xs text-muted-foreground mb-2">Equations</p>
          <div className="space-y-1">
            {dsl.equations.map((eq, i) => (
              <p key={i} className="font-mono text-xs text-[var(--neon-purple)] bg-[var(--neon-purple)]/5 px-3 py-1.5 rounded-lg border border-[var(--neon-purple)]/20">
                {eq}
              </p>
            ))}
          </div>
        </div>
      )}

      {/* Raw JSON toggle */}
      <button
        onClick={() => setShowRaw(!showRaw)}
        className="w-full text-left text-xs p-2 rounded-xl border border-white/10 hover:border-white/20 flex items-center justify-between text-muted-foreground"
      >
        <span>Raw DSL JSON</span>
        {showRaw ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
      </button>
      {showRaw && (
        <pre className="text-[10px] font-mono text-muted-foreground/70 bg-black/30 rounded-xl p-3 border border-white/10 overflow-auto max-h-64">
          {JSON.stringify(dsl, null, 2)}
        </pre>
      )}

      {/* Runtime Integration Notice */}
      <div className="rounded-xl border border-[var(--neon-cyan)]/20 bg-[var(--neon-cyan)]/5 p-3">
        <p className="text-xs text-[var(--neon-cyan)]/80 flex items-center gap-2">
          <Zap className="w-3.5 h-3.5 flex-shrink-0" />
          Physics DSL compiled successfully. Runtime interpreter will execute interactions and render the simulation.
        </p>
      </div>
    </div>
  );
}

// =========================================================
// Main Page
// =========================================================

function AIAgentPage() {
  const {
    simulation,
    loading,
    streaming,
    error,
    progress,
    progressPercentage,
    generate,
    generateStream,
    clearError,
  } = useAgentSimulation();

  const [prompt, setPrompt] = useState("");
  const [useStreaming, setUseStreaming] = useState(true);
  const [complexity, setComplexity] = useState<"beginner" | "medium" | "advanced">("medium");

  const handleGenerate = async () => {
    if (!prompt.trim()) return;
    if (useStreaming) {
      await generateStream(prompt, complexity);
    } else {
      await generate(prompt, complexity);
    }
  };

  const handleShare = async () => {
    if (!simulation?.id) return;
    const shareUrl = `${window.location.origin}/ai-agent?sim=${simulation.id}`;
    try {
      await navigator.clipboard.writeText(shareUrl);
      alert("Share link copied to clipboard!");
    } catch {
      alert("Failed to copy share link");
    }
  };

  const handleExportDSL = () => {
    if (!simulation?.dsl) return;
    const blob = new Blob([JSON.stringify(simulation.dsl, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${simulation.id ?? "simulation"}.dsl.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <PageWrapper>
      <div className="space-y-4">
        {/* Header */}
        <div className="glass-strong rounded-3xl p-6 md:p-8">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h1 className="text-3xl font-bold text-gradient mb-2">
                Autonomous AI Simulation Agent
              </h1>
              <p className="text-sm text-muted-foreground max-w-2xl">
                Generate interactive physics, chemistry, and mathematics simulations from natural
                language. The agent analyzes your prompt, retrieves textbook context, and compiles
                a validated Physics DSL for runtime execution.
              </p>
            </div>
            <Sparkles className="w-8 h-8 text-[var(--neon-purple)] flex-shrink-0" />
          </div>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-[380px_1fr] gap-4">
          {/* Left Panel: Controls */}
          <div className="glass-strong rounded-3xl p-4 space-y-4 h-fit">
            <div>
              <label className="text-xs uppercase tracking-wide text-muted-foreground flex items-center gap-2 mb-2">
                <Lightbulb className="w-4 h-4" /> Your Idea
              </label>
              <Textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="E.g., Create a projectile motion simulation with adjustable angle and velocity..."
                className="min-h-32 bg-slate-900/50 border-white/10"
                disabled={loading}
              />
            </div>

            <div>
              <label className="text-xs uppercase tracking-wide text-muted-foreground flex items-center gap-2 mb-2">
                <Settings2 className="w-4 h-4" /> Complexity Level
              </label>
              <div className="grid grid-cols-3 gap-2">
                {(["beginner", "medium", "advanced"] as const).map((level) => (
                  <button
                    key={level}
                    onClick={() => setComplexity(level)}
                    className={`px-3 py-2 text-xs font-semibold rounded-xl border transition-all ${
                      complexity === level
                        ? "bg-[var(--neon-cyan)] text-black border-[var(--neon-cyan)]"
                        : "border-white/10 hover:border-white/30 text-muted-foreground"
                    }`}
                    disabled={loading}
                  >
                    {level.charAt(0).toUpperCase() + level.slice(1)}
                  </button>
                ))}
              </div>
            </div>

            <Button
              onClick={handleGenerate}
              disabled={loading || !prompt.trim()}
              className="w-full bg-gradient-to-r from-[var(--neon-purple)] to-[var(--neon-blue)] text-base"
              size="lg"
            >
              <Sparkles className="w-4 h-4 mr-2" />
              {loading
                ? streaming
                  ? "Compiling DSL..."
                  : "Processing..."
                : "Generate Simulation"}
            </Button>

            {/* Streaming Toggle */}
            <button
              onClick={() => setUseStreaming(!useStreaming)}
              className="w-full text-left text-xs p-3 rounded-xl border border-white/10 hover:border-white/30 transition-colors"
            >
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Streaming Mode</span>
                <span className={`font-semibold ${useStreaming ? "text-[var(--neon-cyan)]" : "text-muted-foreground"}`}>
                  {useStreaming ? "ON" : "OFF"}
                </span>
              </div>
            </button>

            {/* Example Prompts */}
            <div className="space-y-2">
              <p className="text-xs text-muted-foreground flex items-center gap-2">
                <BookOpen className="w-4 h-4" /> Example Prompts
              </p>
              {EXAMPLE_PROMPTS.map((example) => (
                <button
                  key={example.title}
                  onClick={() => { setPrompt(example.prompt); clearError(); }}
                  className="w-full text-left p-2 rounded-xl border border-white/10 hover:border-[var(--neon-cyan)]/50 hover:bg-white/5 transition-colors text-xs"
                >
                  <div className="font-semibold text-white">{example.title}</div>
                  <div className="text-muted-foreground text-xs line-clamp-1">{example.prompt}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Right Panel: DSL Output */}
          <div className="glass-strong rounded-3xl p-4 space-y-3">
            {/* Title and Actions */}
            <div className="flex items-start justify-between gap-3 flex-wrap">
              <div className="flex-1">
                <h2 className="text-xl font-bold text-white">
                  {simulation?.title || "Awaiting Generation"}
                </h2>
                <p className="text-xs text-muted-foreground mt-1">
                  {simulation?.description || "Your generated simulation will appear here"}
                </p>
              </div>
              {simulation && (
                <div className="flex items-center gap-2">
                  <Button size="sm" variant="outline" onClick={handleShare}>
                    <Link2 className="w-4 h-4 mr-1" /> Share
                  </Button>
                  <Button size="sm" variant="outline" onClick={handleExportDSL}>
                    <Download className="w-4 h-4 mr-1" /> Export DSL
                  </Button>
                </div>
              )}
            </div>

            {/* Progress Display */}
            {(loading || streaming || progress) && (
              <div className="rounded-2xl border border-[var(--neon-purple)]/30 bg-[var(--neon-purple)]/10 p-4 space-y-3">
                <ProgressBar percentage={progressPercentage} stage={progress?.stage || null} />
                <StageIndicator stages={DSL_STAGES} currentStage={progress?.stage || null} />
              </div>
            )}

            {/* Error Display */}
            {error && (
              <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-4">
                <p className="text-sm text-red-200 flex items-start gap-3">
                  <span className="text-red-400 mt-0.5">⚠</span>
                  <span>{error}</span>
                </p>
                <button onClick={clearError} className="text-xs text-red-300 hover:text-red-200 mt-2 underline">
                  Dismiss
                </button>
              </div>
            )}

            {/* DSL Inspector or Empty State */}
            <div className="rounded-2xl border border-white/10 overflow-hidden min-h-[500px] bg-black/30 p-4">
              {simulation?.dsl ? (
                <DSLInspector dsl={simulation.dsl} />
              ) : (
                <div className="h-[500px] flex flex-col items-center justify-center text-center p-6">
                  <PlayCircle className="w-12 h-12 text-muted-foreground/30 mb-3" />
                  <p className="text-muted-foreground mb-2">
                    {loading || streaming
                      ? "Compiling Physics DSL..."
                      : "Generated simulation will appear here"}
                  </p>
                  {!loading && !streaming && (
                    <p className="text-xs text-muted-foreground">
                      Enter a prompt above and click "Generate Simulation" to begin
                    </p>
                  )}
                </div>
              )}
            </div>

            {/* Textbook Sources */}
            {simulation?.context?.sources && simulation.context.sources.length > 0 && (
              <div className="rounded-2xl border border-white/10 p-3">
                <p className="text-xs text-muted-foreground mb-2">Textbook Sources</p>
                <div className="text-xs space-y-1">
                  {simulation.context.sources.slice(0, 3).map((source, i) => (
                    <div key={i} className="text-muted-foreground/70">
                      {source.source} (p. {source.page})
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Formula */}
            {simulation?.formula && (
              <div className="rounded-2xl border border-[var(--neon-purple)]/30 bg-[var(--neon-purple)]/10 p-3">
                <p className="text-xs text-muted-foreground mb-1">Key Formula</p>
                <p className="font-mono text-sm text-[var(--neon-purple)]">{simulation.formula}</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </PageWrapper>
  );
}

