import { Link } from "@tanstack/react-router";
import { motion } from "framer-motion";
import {
  Bot,
  BookOpen,
  BrainCircuit,
  ChevronRight,
  Lightbulb,
  Sparkles,
  Target,
  Zap,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import {
  LAW_ROUTE_BY_KEY,
  type LawKey,
  type LearningMode,
  type LawMetric,
  type LawTutorInsight,
} from "@/types/lawsOfMotion";

export const LAW_NAV = [
  { key: "first-law" as const, label: "First Law", short: "Inertia" },
  { key: "second-law" as const, label: "Second Law", short: "F = ma" },
  { key: "third-law" as const, label: "Third Law", short: "Action-Reaction" },
];

export const LEARNING_MODES: Array<{ key: LearningMode; label: string; icon: string }> = [
  { key: "visual", label: "Visual Learning", icon: "👁️" },
  { key: "interactive", label: "Interactive Experiment", icon: "🧪" },
  { key: "real-life", label: "Real-Life Examples", icon: "🏙️" },
  { key: "formula", label: "Formula Breakdown", icon: "∑" },
  { key: "gamified", label: "Gamified Learning", icon: "🎮" },
];

type PromptCardProps = {
  title: string;
  description: string;
  prompt: string;
  setPrompt: (value: string) => void;
  loading: boolean;
  examples: string[];
  history: string[];
  onGenerate: () => void;
  onSelectExample: (value: string) => void;
  onSelectHistory: (value: string) => void;
  onClearHistory: () => void;
};

export function PromptCard({
  title,
  description,
  prompt,
  setPrompt,
  loading,
  examples,
  history,
  onGenerate,
  onSelectExample,
  onSelectHistory,
  onClearHistory,
}: PromptCardProps) {
  return (
    <div className="glass-strong rounded-3xl border border-white/10 p-5 space-y-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-xs uppercase tracking-[0.3em] text-[var(--neon-cyan)] mb-2">
            AI Tutor
          </div>
          <h3 className="text-lg font-bold text-foreground">{title}</h3>
          <p className="text-sm text-muted-foreground mt-1">{description}</p>
        </div>
        <div className="rounded-2xl bg-gradient-to-br from-[var(--neon-purple)]/30 to-[var(--neon-cyan)]/20 p-3">
          <BrainCircuit className="h-5 w-5 text-[var(--neon-cyan)]" />
        </div>
      </div>

      <div className="relative">
        <Textarea
          value={prompt}
          onChange={(event) => setPrompt(event.target.value)}
          placeholder="Ask the lab to generate or explain an experiment..."
          className="min-h-28 resize-none border-white/10 bg-white/5 text-white placeholder:text-white/30"
        />
      </div>

      <div className="flex gap-2 flex-wrap">
        <Button
          onClick={onGenerate}
          disabled={loading || !prompt.trim()}
          className="bg-gradient-to-r from-[var(--neon-purple)] to-[var(--neon-blue)] text-white shadow-lg shadow-[var(--neon-purple)]/20"
        >
          <Sparkles className="mr-2 h-4 w-4" />
          {loading ? "Generating..." : "Generate"}
        </Button>
        <Button
          variant="outline"
          className="border-white/10 bg-white/5 text-foreground hover:bg-white/10"
          onClick={() => setPrompt("")}
          disabled={loading}
        >
          Clear
        </Button>
      </div>

      <div className="space-y-2">
        <div className="text-xs uppercase tracking-[0.3em] text-muted-foreground">
          Example prompts
        </div>
        <div className="flex flex-wrap gap-2">
          {examples.map((example) => (
            <button
              key={example}
              onClick={() => onSelectExample(example)}
              className="rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-slate-200 transition hover:border-[var(--neon-cyan)]/40 hover:text-white"
            >
              {example}
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <div className="text-xs uppercase tracking-[0.3em] text-muted-foreground">
            Prompt history
          </div>
          <button
            onClick={onClearHistory}
            className="text-xs text-[var(--neon-cyan)] hover:underline"
          >
            Clear
          </button>
        </div>
        <div className="space-y-2">
          {history.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-white/10 bg-white/5 p-3 text-xs text-muted-foreground">
              No prompts yet. Try one of the examples.
            </div>
          ) : (
            history.slice(0, 6).map((item) => (
              <button
                key={item}
                onClick={() => onSelectHistory(item)}
                className="flex w-full items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-3 py-2 text-left text-xs text-slate-200 transition hover:border-[var(--neon-purple)]/40 hover:bg-white/10"
              >
                <span className="line-clamp-1">{item}</span>
                <ChevronRight className="h-3.5 w-3.5 shrink-0 text-[var(--neon-cyan)]" />
              </button>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

type TutorCardProps = {
  title: string;
  subtitle: string;
  response: string;
  question: string;
  setQuestion: (value: string) => void;
  onAsk: () => void;
  askLoading?: boolean;
  hints: string[];
  insights?: LawTutorInsight;
  followUpLabel?: string;
};

export function TutorCard({
  title,
  subtitle,
  response,
  question,
  setQuestion,
  onAsk,
  askLoading,
  hints,
  insights,
  followUpLabel = "Follow-up questions",
}: TutorCardProps) {
  return (
    <div className="glass-strong rounded-3xl border border-white/10 p-5 space-y-4">
      <div className="flex items-center gap-3">
        <div className="rounded-2xl bg-gradient-to-br from-[var(--neon-cyan)]/25 to-[var(--neon-blue)]/15 p-3">
          <Bot className="h-5 w-5 text-[var(--neon-cyan)]" />
        </div>
        <div>
          <div className="text-xs uppercase tracking-[0.3em] text-[var(--neon-cyan)]">AI Tutor</div>
          <h3 className="text-lg font-bold text-foreground">{title}</h3>
          <p className="text-sm text-muted-foreground">{subtitle}</p>
        </div>
      </div>

      <div className="rounded-2xl border border-white/10 bg-black/20 p-4 text-sm text-slate-200 min-h-28 whitespace-pre-line">
        {response || "Ask a why question or trigger a simulation to see live guidance here."}
      </div>

      {insights ? (
        <div className="grid gap-3 md:grid-cols-2">
          <div className="rounded-2xl border border-[var(--neon-cyan)]/20 bg-[var(--neon-cyan)]/5 p-3 text-xs text-slate-200">
            <div className="mb-1 text-[10px] uppercase tracking-[0.3em] text-[var(--neon-cyan)]">
              Why this happened
            </div>
            <div className="leading-6">{insights.whyThisHappened}</div>
          </div>
          <div className="rounded-2xl border border-[var(--neon-purple)]/20 bg-[var(--neon-purple)]/5 p-3 text-xs text-slate-200">
            <div className="mb-1 text-[10px] uppercase tracking-[0.3em] text-[var(--neon-cyan)]">
              Adaptive explanation
            </div>
            <div className="leading-6">{insights.adaptiveExplanation}</div>
          </div>
        </div>
      ) : null}

      <div className="flex gap-2">
        <Textarea
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Why does acceleration decrease when mass increases?"
          className="min-h-20 resize-none border-white/10 bg-white/5 text-white placeholder:text-white/30"
        />
      </div>
      <Button
        onClick={onAsk}
        disabled={askLoading || !question.trim()}
        className="w-full bg-gradient-to-r from-[var(--neon-cyan)] to-[var(--neon-blue)] text-slate-950 font-semibold"
      >
        <Lightbulb className="mr-2 h-4 w-4" />
        {askLoading ? "Thinking..." : "Ask Tutor"}
      </Button>

      <div className="space-y-2">
        <div className="text-xs uppercase tracking-[0.3em] text-muted-foreground">Hints</div>
        {hints.map((hint) => (
          <div
            key={hint}
            className="flex items-start gap-2 rounded-2xl border border-white/10 bg-white/5 px-3 py-2 text-xs text-slate-200"
          >
            <Zap className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[var(--neon-cyan)]" />
            <span>{hint}</span>
          </div>
        ))}
      </div>

      {insights ? (
        <div className="space-y-2">
          <div className="text-xs uppercase tracking-[0.3em] text-muted-foreground">
            {followUpLabel}
          </div>
          <div className="flex flex-wrap gap-2">
            {insights.followUpQuestions.map((item) => (
              <span
                key={item}
                className="rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-[11px] text-slate-200"
              >
                {item}
              </span>
            ))}
          </div>
          <div className="text-xs uppercase tracking-[0.3em] text-muted-foreground">
            Recommendations
          </div>
          <div className="flex flex-wrap gap-2">
            {insights.recommendations.map((item) => (
              <span
                key={item}
                className="rounded-full border border-[var(--neon-cyan)]/20 bg-[var(--neon-cyan)]/10 px-3 py-1.5 text-[11px] text-[var(--neon-cyan)]"
              >
                {item}
              </span>
            ))}
          </div>
          {insights.mistakeDetection.length > 0 ? (
            <div className="rounded-2xl border border-amber-400/20 bg-amber-400/5 p-3 text-xs text-slate-200">
              <div className="mb-1 text-[10px] uppercase tracking-[0.3em] text-amber-300">
                Possible mistake
              </div>
              <div>{insights.mistakeDetection.join(" · ")}</div>
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

type FormulaCardProps = {
  formula: string;
  breakdown: string[];
  mode: LearningMode;
  scene: string;
};

export function FormulaCard({ formula, breakdown, mode, scene }: FormulaCardProps) {
  return (
    <div className="glass-strong rounded-3xl border border-white/10 p-5 space-y-4">
      <div className="flex items-center gap-3">
        <div className="rounded-2xl bg-gradient-to-br from-[var(--neon-purple)]/25 to-[var(--neon-cyan)]/15 p-3">
          <BookOpen className="h-5 w-5 text-[var(--neon-purple)]" />
        </div>
        <div>
          <div className="text-xs uppercase tracking-[0.3em] text-[var(--neon-cyan)]">
            Formula panel
          </div>
          <h3 className="text-lg font-bold text-foreground">{formula}</h3>
          <p className="text-sm text-muted-foreground">
            Mode: {mode} · Scene: {scene}
          </p>
        </div>
      </div>
      <div className="rounded-2xl border border-white/10 bg-black/20 p-4 text-sm text-slate-200 space-y-2">
        {breakdown.map((line) => (
          <div key={line} className="flex items-start gap-2">
            <Target className="mt-0.5 h-4 w-4 shrink-0 text-[var(--neon-cyan)]" />
            <span>{line}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

type LearningModePickerProps = {
  mode: LearningMode;
  onChange: (mode: LearningMode) => void;
};

export function LearningModePicker({ mode, onChange }: LearningModePickerProps) {
  return (
    <div className="glass-strong rounded-3xl border border-white/10 p-4 space-y-3">
      <div className="text-xs uppercase tracking-[0.3em] text-muted-foreground">Learning mode</div>
      <div className="grid grid-cols-2 gap-2">
        {LEARNING_MODES.map((item) => (
          <button
            key={item.key}
            onClick={() => onChange(item.key)}
            className={cn(
              "rounded-2xl border px-3 py-3 text-left text-sm transition",
              mode === item.key
                ? "border-[var(--neon-cyan)]/60 bg-[var(--neon-cyan)]/10 text-white shadow-[0_0_20px_rgba(34,211,238,0.12)]"
                : "border-white/10 bg-white/5 text-slate-200 hover:border-white/20 hover:bg-white/10",
            )}
          >
            <div className="text-base">{item.icon}</div>
            <div className="mt-1 text-xs font-semibold uppercase tracking-[0.2em]">
              {item.label}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}

type MetricStripProps = {
  metrics: LawMetric[];
};

export function MetricStrip({ metrics }: MetricStripProps) {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
      {metrics.map((metric) => (
        <div key={metric.label} className="glass rounded-2xl border border-white/10 p-3">
          <div className="text-[10px] uppercase tracking-[0.3em] text-muted-foreground">
            {metric.label}
          </div>
          <div className="mt-1 flex items-baseline gap-1">
            <span
              className="text-xl font-bold font-mono"
              style={{ color: metric.color, textShadow: `0 0 12px ${metric.color}` }}
            >
              {metric.value}
            </span>
            <span className="text-xs text-muted-foreground">{metric.unit}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

type LawTabsProps = {
  active: LawKey;
};

export function LawTabs({ active }: LawTabsProps) {
  return (
    <div className="flex flex-wrap gap-2 rounded-3xl border border-white/10 bg-white/5 p-2">
      {LAW_NAV.map((item) => (
        <Link
          key={item.key}
          to={LAW_ROUTE_BY_KEY[item.key]}
          className={cn(
            "rounded-2xl px-4 py-2 text-sm font-medium transition",
            active === item.key
              ? "bg-gradient-to-r from-[var(--neon-purple)] to-[var(--neon-blue)] text-white shadow-lg shadow-[var(--neon-purple)]/20"
              : "text-slate-200 hover:bg-white/10",
          )}
        >
          <div className="flex items-center gap-2">
            <span>{item.label}</span>
            <span className="hidden md:inline text-[10px] uppercase tracking-[0.3em] text-white/60">
              {item.short}
            </span>
          </div>
        </Link>
      ))}
    </div>
  );
}

export const ENVIRONMENTS = [
  { key: "lab", label: "Lab", icon: "🔬" },
  { key: "space", label: "Space", icon: "🚀" },
  { key: "road", label: "Street", icon: "🛣️" },
  { key: "ice", label: "Sports", icon: "⛸️" },
  { key: "construction", label: "Construction", icon: "🏗️" },
  { key: "underwater", label: "Underwater", icon: "🌊" },
  { key: "mountain", label: "Mountain", icon: "⛰️" },
];

export function EnvironmentPicker({
  environment,
  onChange,
}: {
  environment: string;
  onChange: (env: any) => void;
}) {
  return (
    <div className="glass-strong rounded-3xl border border-white/10 p-5 space-y-4">
      <div className="text-xs uppercase tracking-[0.3em] text-muted-foreground">
        Environment Theme
      </div>
      <div className="flex flex-wrap gap-2">
        {ENVIRONMENTS.map((item) => (
          <button
            key={item.key}
            onClick={() => onChange(item.key)}
            className={cn(
              "rounded-full border px-3 py-1.5 text-xs transition flex items-center gap-1.5",
              environment === item.key
                ? "border-[var(--neon-cyan)]/60 bg-[var(--neon-cyan)]/10 text-white shadow-[0_0_10px_rgba(34,211,238,0.12)]"
                : "border-white/10 bg-white/5 text-slate-300 hover:border-white/20 hover:text-white hover:bg-white/10",
            )}
          >
            <span>{item.icon}</span>
            <span>{item.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
