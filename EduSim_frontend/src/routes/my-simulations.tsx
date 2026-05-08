import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import { PageWrapper } from "@/components/Card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Sparkles, PlayCircle, Link2, Download, Database } from "lucide-react";
import {
  simulationSynthesisService,
  SynthesizedSimulation,
} from "@/services/simulationSynthesisService";

export const Route = createFileRoute("/my-simulations")({
  component: MySimulationsPage,
});

const EXAMPLES = [
  "Explain projectile motion with simulation",
  "Generate a pendulum experiment",
  "Show momentum conservation",
  "Visualize electric field lines",
];

function isClientSafeHtml(html: string): boolean {
  const blocked = [
    /<script[^>]+src\s*=/i,
    /https?:\/\//i,
    /\bfetch\s*\(/i,
    /XMLHttpRequest/i,
    /WebSocket/i,
    /window\.open/i,
    /\btop\./i,
    /\bparent\./i,
    /\beval\s*\(/i,
    /new\s+Function\s*\(/i,
  ];

  return !blocked.some((pattern) => pattern.test(html));
}

function MySimulationsPage() {
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [items, setItems] = useState<SynthesizedSimulation[]>([]);
  const [active, setActive] = useState<SynthesizedSimulation | null>(null);
  const [progress, setProgress] = useState<string | null>(null);
  const [useStreaming, setUseStreaming] = useState(true);

  const activeHtml = useMemo(() => {
    if (!active?.html) {
      return "";
    }
    return isClientSafeHtml(active.html) ? active.html : "";
  }, [active]);

  const loadList = async () => {
    const list = await simulationSynthesisService.list(40);
    setItems(list);
    if (!active && list.length > 0) {
      setActive(list[0]);
    }
  };

  const loadById = async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      const item = await simulationSynthesisService.getById(id);
      if (!isClientSafeHtml(item.html || "")) {
        throw new Error("Blocked unsafe generated HTML in client safety check.");
      }
      setActive(item);
    } catch (err: any) {
      setError(err.message || "Failed to load simulation.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const initialize = async () => {
      setLoading(true);
      setError(null);
      try {
        await loadList();
        const id = new URLSearchParams(window.location.search).get("id");
        if (id) {
          await loadById(id);
        }
      } catch (err: any) {
        setError(err.message || "Failed to initialize synthesis system.");
      } finally {
        setLoading(false);
      }
    };

    initialize();
  }, []);

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      return;
    }

    setLoading(true);
    setError(null);
    setProgress(null);

    try {
      if (useStreaming) {
        // Streaming generation with progress updates
        await simulationSynthesisService.generateStream(
          prompt.trim(),
          (progress) => {
            if (progress.error) {
              setError(`Error: ${progress.error}`);
              setProgress(null);
            } else {
              setProgress(progress.stage);
            }
          },
          (simulation) => {
            if (!isClientSafeHtml(simulation.html || "")) {
              setError("Generated simulation was blocked by client safety checks.");
            } else {
              setActive(simulation);
              setPrompt("");
              setProgress(null);
              loadList();
            }
          }
        );
      } else {
        // Regular generation (non-streaming)
        const generated = await simulationSynthesisService.generate(prompt.trim());
        if (!isClientSafeHtml(generated.html || "")) {
          throw new Error("Generated simulation was blocked by client safety checks.");
        }

        setActive(generated);
        setPrompt("");
        await loadList();
      }
    } catch (err: any) {
      setError(err.message || "Failed to generate simulation.");
      setProgress(null);
    } finally {
      setLoading(false);
    }
  };

  const handleShare = async () => {
    if (!active?.id) {
      return;
    }

    const shareUrl = `${window.location.origin}/my-simulations?id=${active.id}`;
    try {
      await navigator.clipboard.writeText(shareUrl);
    } catch {
      setError("Failed to copy share URL to clipboard.");
    }
  };

  const handleExport = () => {
    if (!active?.id) {
      return;
    }
    window.open(simulationSynthesisService.getExportUrl(active.id), "_blank", "noopener,noreferrer");
  };

  return (
    <PageWrapper>
      <div className="space-y-4">
        <div className="glass-strong rounded-3xl p-6 md:p-8">
          <h1 className="text-3xl font-bold text-gradient mb-2">Simulation Synthesis System</h1>
          <p className="text-sm text-muted-foreground">
            Generate textbook-grounded, AI-powered simulations and run them safely in sandboxed
            mode.
          </p>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-[360px_1fr] gap-4">
          <div className="glass-strong rounded-3xl p-4 space-y-4">
            <div>
              <label className="text-xs uppercase tracking-wide text-muted-foreground">
                Prompt
              </label>
              <Textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Explain projectile motion with simulation"
                className="mt-2 min-h-24 bg-slate-900/50 border-white/10"
                disabled={loading}
              />
            </div>

            <Button
              onClick={handleGenerate}
              disabled={loading || !prompt.trim()}
              className="w-full bg-gradient-to-r from-[var(--neon-purple)] to-[var(--neon-blue)]"
            >
              <Sparkles className="w-4 h-4 mr-2" />
              {loading ? (progress ? `${progress}...` : "Synthesizing...") : "Synthesize Simulation"}
            </Button>

            <button
              onClick={() => setUseStreaming(!useStreaming)}
              className="w-full text-left text-xs p-2 rounded-xl border border-white/10 hover:border-white/30 transition-colors"
            >
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Streaming Mode</span>
                <span className={`font-semibold ${useStreaming ? "text-[var(--neon-cyan)]" : "text-muted-foreground"}`}>
                  {useStreaming ? "ON" : "OFF"}
                </span>
              </div>
            </button>

            <div className="space-y-2">
              <p className="text-xs text-muted-foreground">Try examples</p>
              {EXAMPLES.map((example) => (
                <button
                  key={example}
                  onClick={() => setPrompt(example)}
                  className="w-full text-left text-xs p-2 rounded-xl border border-white/10 hover:border-[var(--neon-cyan)]/50 hover:bg-white/5"
                >
                  {example}
                </button>
              ))}
            </div>

            <div className="pt-2 border-t border-white/10">
              <div className="flex items-center gap-2 text-xs text-muted-foreground mb-2">
                <Database className="w-4 h-4" />
                Saved Simulations
              </div>
              <div className="space-y-2 max-h-64 overflow-auto pr-1">
                {items.map((item) => (
                  <button
                    key={item.id}
                    onClick={() => loadById(item.id)}
                    className={`w-full text-left p-2 rounded-xl border text-xs transition-colors ${
                      active?.id === item.id
                        ? "border-[var(--neon-cyan)] bg-[var(--neon-cyan)]/10"
                        : "border-white/10 hover:border-white/30"
                    }`}
                  >
                    <div className="font-semibold truncate">{item.title}</div>
                    <div className="text-muted-foreground truncate">{item.prompt}</div>
                  </button>
                ))}
                {items.length === 0 && (
                  <p className="text-xs text-muted-foreground">No synthesized simulations yet.</p>
                )}
              </div>
            </div>
          </div>

          <div className="glass-strong rounded-3xl p-4 space-y-3">
            <div className="flex items-center justify-between gap-2 flex-wrap">
              <div>
                <h2 className="text-lg font-semibold">{active?.title || "Awaiting Synthesis"}</h2>
                <p className="text-xs text-muted-foreground">{active?.description || "No simulation selected"}</p>
              </div>
              <div className="flex items-center gap-2">
                <Button size="sm" variant="outline" onClick={handleShare} disabled={!active?.id}>
                  <Link2 className="w-4 h-4 mr-1" /> Share
                </Button>
                <Button size="sm" variant="outline" onClick={handleExport} disabled={!active?.id}>
                  <Download className="w-4 h-4 mr-1" /> Export
                </Button>
              </div>
            </div>

            {active?.formula && (
              <div className="rounded-2xl border border-[var(--neon-cyan)]/30 bg-[var(--neon-cyan)]/10 p-3 text-xs font-mono">
                Formula: {active.formula}
              </div>
            )}

            <div className="rounded-2xl border border-white/10 overflow-hidden min-h-[520px] bg-black/30">
              {activeHtml ? (
                <iframe
                  title={active?.title || "Synthesized Simulation"}
                  sandbox="allow-scripts"
                  srcDoc={activeHtml}
                  className="w-full min-h-[520px] border-0"
                />
              ) : (
                <div className="h-[520px] flex items-center justify-center text-center p-6 text-muted-foreground">
                  <div>
                    <PlayCircle className="mx-auto mb-2 w-8 h-8" />
                    <p>Generated simulation will appear here.</p>
                  </div>
                </div>
              )}
            </div>

            <div className="text-xs text-muted-foreground">
              Sources: {active?.sources?.map((s) => `${s.source} (p.${s.page})`).join(", ") || "No textbook sources available"}
            </div>

            {error && (
              <div className="rounded-2xl border border-red-500/40 bg-red-500/10 p-3 text-xs text-red-300">
                {error}
              </div>
            )}
          </div>
        </div>
      </div>
    </PageWrapper>
  );
}

export function Stub(title: string, subtitle: string) {
  return (
    <PageWrapper>
      <div className="glass-strong rounded-3xl p-12 text-center">
        <h1 className="text-3xl font-bold text-gradient mb-2">{title}</h1>
        <p className="text-muted-foreground">{subtitle}</p>
      </div>
    </PageWrapper>
  );
}
