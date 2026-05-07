import type { ReactNode } from "react";
import { Play, Pause, RotateCcw, Eye, EyeOff, Lightbulb } from "lucide-react";

type SliderDef = {
  label: string;
  value: number;
  min: number;
  max: number;
  step?: number;
  unit: string;
  color: string;
  onChange: (v: number) => void;
};

type Props = {
  title: string;
  sliders: SliderDef[];
  formulaTitle: string;
  formula: string;
  liveEquation: string;
  showVectors: boolean;
  setShowVectors: (v: boolean) => void;
  running: boolean;
  onPlay: () => void;
  onPause: () => void;
  onReset: () => void;
  onAction?: { label: string; icon: ReactNode; onClick: () => void };
  onExplain: () => void;
};

export function LawControls({
  title, sliders, formulaTitle, formula, liveEquation,
  showVectors, setShowVectors, running, onPlay, onPause, onReset,
  onAction, onExplain,
}: Props) {
  return (
    <div className="glass-strong rounded-3xl p-5 space-y-5 h-full">
      {/* Sliders */}
      <div>
        <h3 className="text-sm font-bold uppercase tracking-widest text-muted-foreground mb-3">{title}</h3>
        <div className="space-y-3">
          {sliders.map((s) => (
            <label key={s.label} className="block space-y-1">
              <div className="flex justify-between text-xs">
                <span className="text-muted-foreground">{s.label}</span>
                <span className="font-mono font-semibold" style={{ color: s.color, textShadow: `0 0 8px ${s.color}` }}>
                  {s.value.toFixed(s.step && s.step < 0.1 ? 2 : 1)} <span className="text-[10px] text-muted-foreground">{s.unit}</span>
                </span>
              </div>
              <input
                type="range" min={s.min} max={s.max} step={s.step ?? 0.5} value={s.value}
                onChange={(e) => s.onChange(Number(e.target.value))}
                className="w-full h-1.5 rounded-full cursor-pointer accent-[var(--neon-cyan)]"
              />
            </label>
          ))}
        </div>
      </div>

      {/* Buttons */}
      <div className="space-y-2">
        <button
          onClick={running ? onPause : onPlay}
          className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-2xl bg-gradient-to-r from-[var(--neon-purple)] to-[var(--neon-blue)] text-white font-medium hover:opacity-90 transition"
        >
          {running ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
          {running ? "Pause" : "Play"}
        </button>
        <div className="grid grid-cols-2 gap-2">
          <button onClick={onReset} className="flex items-center justify-center gap-1 px-3 py-2 rounded-2xl glass text-sm hover:neon-border transition">
            <RotateCcw className="w-3.5 h-3.5" /> Reset
          </button>
          <button onClick={() => setShowVectors(!showVectors)} className="flex items-center justify-center gap-1 px-3 py-2 rounded-2xl glass text-sm hover:neon-border transition">
            {showVectors ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />} Vectors
          </button>
        </div>
        {onAction && (
          <button onClick={onAction.onClick} className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-2xl glass text-sm font-medium hover:neon-border transition">
            {onAction.icon} {onAction.label}
          </button>
        )}
      </div>

      {/* Formula */}
      <div className="border-t border-white/10 pt-4 space-y-3">
        <h3 className="text-sm font-bold uppercase tracking-widest text-muted-foreground">{formulaTitle}</h3>
        <div className="glass rounded-xl px-3 py-2">
          <div className="font-mono text-lg text-[var(--neon-cyan)] text-center" style={{ textShadow: "0 0 16px rgba(34,211,238,0.3)" }}>{formula}</div>
        </div>
        <div className="glass rounded-xl px-3 py-2 text-xs font-mono text-muted-foreground text-center">{liveEquation}</div>
        <button onClick={onExplain}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-2xl bg-[var(--neon-cyan)]/15 text-[var(--neon-cyan)] text-sm hover:bg-[var(--neon-cyan)]/25 transition-colors">
          <Lightbulb className="w-4 h-4" /> Explain Concept
        </button>
      </div>
    </div>
  );
}
