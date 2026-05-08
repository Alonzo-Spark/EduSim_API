import { createFileRoute } from "@tanstack/react-router";
import { useState, useMemo, useEffect } from "react";
import { PageWrapper } from "@/components/Card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  Sparkles,
  PlayCircle,
  Link2,
  Download,
  Zap,
  BookOpen,
  Lightbulb,
  Settings2,
} from "lucide-react";
import { useAgentSimulation } from "@/hooks/useAgentSimulation";
import { agentSimulationService } from "@/services/agentSimulationService";

export const Route = createFileRoute("/ai-agent")({
  component: AIAgentPage,
});

const EXAMPLE_PROMPTS = [
  {
    title: "Projectile Motion",
    prompt: "Create a projectile motion simulation showing trajectory with adjustable angle and velocity",
  },
  {
    title: "Newton's Third Law",
    prompt: "Visualize Newton's Third Law of Motion with interactive force demonstrations",
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

const GENERATION_STAGES = [
  "Analyzing prompt",
  "Detecting subject",
  "Retrieving textbook context",
  "Extracting formulas",
  "Generating simulation logic",
  "Synthesizing interactive visuals",
  "Validating HTML safety",
  "Sanitizing content",
  "Injecting security policy",
  "Rendering simulation",
];

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
        {stages.map((stage, index) => {
          const isActive = currentStage?.includes(stage);
          const isCompleted = currentStage
            ? stages.indexOf(stage) < stages.indexOf(stage)
            : false;

          return (
            <div
              key={stage}
              className={`px-2 py-1 rounded-full text-xs transition-colors whitespace-nowrap ${
                isActive
                  ? "bg-[var(--neon-cyan)] text-black font-semibold"
                  : isCompleted
                    ? "bg-[var(--neon-purple)]/50 text-white"
                    : "bg-slate-900/50 text-muted-foreground border border-white/10"
              }`}
            >
              {stage.split(" ")[0]}
            </div>
          );
        })}
      </div>
    </div>
  );
}

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

  const simulationHtml = useMemo(() => {
    if (!simulation?.html) return "";
    return simulation.html;
  }, [simulation?.html]);

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

  // Listen for runtime error messages posted from the iframe and forward to backend
  useEffect(() => {
    function handleMessage(e: MessageEvent) {
      try {
        const data = e.data || {};
        if (data?.type === "sim_error") {
          // Forward to backend for auto-repair and logging
          agentSimulationService.reportRuntimeError(simulation?.id || null, data);
        }
      } catch (err) {
        console.error("Failed to handle iframe message", err);
      }
    }

    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, [simulation?.id]);

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
                language. The agent analyzes your prompt, retrieves textbook context, and creates
                complete educational simulations.
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
                  ? "Generating..."
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
                <span
                  className={`font-semibold ${
                    useStreaming ? "text-[var(--neon-cyan)]" : "text-muted-foreground"
                  }`}
                >
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
                  onClick={() => {
                    setPrompt(example.prompt);
                    clearError();
                  }}
                  className="w-full text-left p-2 rounded-xl border border-white/10 hover:border-[var(--neon-cyan)]/50 hover:bg-white/5 transition-colors text-xs"
                >
                  <div className="font-semibold text-white">{example.title}</div>
                  <div className="text-muted-foreground text-xs line-clamp-1">
                    {example.prompt}
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Right Panel: Simulation */}
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
                </div>
              )}
            </div>

            {/* Progress Display */}
            {(loading || streaming || progress) && (
              <div className="rounded-2xl border border-[var(--neon-purple)]/30 bg-[var(--neon-purple)]/10 p-4 space-y-3">
                <ProgressBar percentage={progressPercentage} stage={progress?.stage || null} />
                <StageIndicator stages={GENERATION_STAGES} currentStage={progress?.stage || null} />
                {progress?.message && (
                  <p className="text-xs text-muted-foreground italic">{progress.message}</p>
                )}
              </div>
            )}

            {/* Error Display */}
            {error && (
              <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-4">
                <p className="text-sm text-red-200 flex items-start gap-3">
                  <span className="text-red-400 mt-0.5">⚠</span>
                  <span>{error}</span>
                </p>
                <button
                  onClick={clearError}
                  className="text-xs text-red-300 hover:text-red-200 mt-2 underline"
                >
                  Dismiss
                </button>
              </div>
            )}

            {/* Metadata Display */}
            {simulation && (
              <>
                {/* Learning Objectives */}
                {simulation.learning_objectives.length > 0 && (
                  <div className="rounded-2xl border border-[var(--neon-cyan)]/30 bg-[var(--neon-cyan)]/10 p-3">
                    <h3 className="text-xs font-semibold text-[var(--neon-cyan)] mb-2 flex items-center gap-2">
                      <Lightbulb className="w-4 h-4" /> Learning Objectives
                    </h3>
                    <ul className="text-xs text-muted-foreground space-y-1">
                      {simulation.learning_objectives.slice(0, 3).map((obj, i) => (
                        <li key={i} className="flex items-start gap-2">
                          <span className="text-[var(--neon-cyan)]">•</span>
                          <span>{obj}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Formula Display */}
                {simulation.formula && (
                  <div className="rounded-2xl border border-[var(--neon-purple)]/30 bg-[var(--neon-purple)]/10 p-3">
                    <p className="text-xs text-muted-foreground mb-1">Key Formula</p>
                    <p className="font-mono text-sm text-[var(--neon-purple)]">{simulation.formula}</p>
                  </div>
                )}

                {/* Related Concepts */}
                {simulation.related_concepts.length > 0 && (
                  <div className="rounded-2xl border border-white/10 p-3">
                    <p className="text-xs text-muted-foreground mb-2">Related Concepts</p>
                    <div className="flex flex-wrap gap-2">
                      {simulation.related_concepts.slice(0, 5).map((concept, i) => (
                        <span
                          key={i}
                          className="px-2 py-1 rounded-full bg-white/5 border border-white/10 text-xs text-muted-foreground"
                        >
                          {concept}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}

            {/* Simulation Canvas */}
            <div className="rounded-2xl border border-white/10 overflow-hidden min-h-[500px] bg-black/50">
              {simulationHtml ? (
                <iframe
                  title={simulation?.title || "Generated Simulation"}
                  sandbox="allow-scripts"
                  srcDoc={simulationHtml}
                  className="w-full min-h-[500px] border-0 bg-black"
                />
              ) : (
                <div className="h-[500px] flex flex-col items-center justify-center text-center p-6">
                  <PlayCircle className="w-12 h-12 text-muted-foreground/30 mb-3" />
                  <p className="text-muted-foreground mb-2">
                    {loading || streaming
                      ? "Your simulation is being generated..."
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

            {/* Sources and Metadata */}
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
          </div>
        </div>
      </div>
    </PageWrapper>
  );
}
