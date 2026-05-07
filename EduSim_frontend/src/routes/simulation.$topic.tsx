import { createFileRoute } from "@tanstack/react-router";
import { motion } from "framer-motion";
import { useState } from "react";
import { PageWrapper } from "@/components/Card";
import { Play, Pause, RotateCcw, Sparkles } from "lucide-react";

export const Route = createFileRoute("/simulation/$topic")({ component: SimulationPage });

function SimulationPage() {
  const { topic } = Route.useParams();
  const decoded = decodeURIComponent(topic);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(50);

  return (
    <PageWrapper>
      <div className="glass-strong rounded-3xl p-5 mb-4 flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-xl font-bold">{decoded}</h1>
          <p className="text-xs text-muted-foreground">Interactive Simulation</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setPlaying((p) => !p)}
            className="w-11 h-11 rounded-2xl bg-gradient-to-br from-[var(--neon-purple)] to-[var(--neon-blue)] flex items-center justify-center text-white glow-purple"
          >
            {playing ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
          </button>
          <button
            onClick={() => setPlaying(false)}
            className="w-11 h-11 rounded-2xl glass flex items-center justify-center hover:text-[var(--neon-cyan)]"
          >
            <RotateCcw className="w-5 h-5" />
          </button>
          <div className="glass rounded-2xl px-4 py-2 flex items-center gap-3">
            <span className="text-xs text-muted-foreground">Speed</span>
            <input
              type="range"
              min={1}
              max={100}
              value={speed}
              onChange={(e) => setSpeed(Number(e.target.value))}
              className="accent-[var(--neon-purple)]"
            />
            <span className="text-xs font-mono w-8 text-right">{speed}</span>
          </div>
        </div>
      </div>

      <div className="grid lg:grid-cols-[2fr_1fr] gap-4">
        <div className="glass-strong rounded-3xl p-6 min-h-[500px] relative overflow-hidden">
          <div className="absolute inset-0 opacity-30 bg-[radial-gradient(circle_at_50%_50%,var(--neon-purple),transparent_60%)]" />
          <div className="relative h-full flex items-center justify-center">
            <motion.div
              animate={playing ? { scale: [1, 1.3, 1], rotate: [0, 360] } : { scale: 1, rotate: 0 }}
              transition={{
                duration: Math.max(0.5, 3 - speed / 40),
                repeat: playing ? Infinity : 0,
                ease: "linear",
              }}
              className="w-40 h-40 rounded-full bg-gradient-to-br from-[var(--neon-purple)] via-[var(--neon-blue)] to-[var(--neon-cyan)] glow-purple flex items-center justify-center"
            >
              <Sparkles className="w-16 h-16 text-white" />
            </motion.div>
          </div>
          <div className="absolute bottom-4 left-4 text-xs font-mono text-muted-foreground">
            SIMULATION CANVAS
          </div>
        </div>

        <div className="glass-strong rounded-3xl p-6 space-y-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-[var(--neon-cyan)] to-[var(--neon-blue)] flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <h2 className="font-bold">Explanation</h2>
          </div>
          <p className="text-sm text-muted-foreground leading-relaxed">
            This panel will host AI-generated, contextual explanations for the running simulation.
            Adjust the controls and watch how the visualization responds in real time.
          </p>
          <div className="space-y-2">
            {[
              "Concept Overview",
              "Step-by-step Walkthrough",
              "Key Formulas",
              "Practice Question",
            ].map((t) => (
              <div
                key={t}
                className="glass rounded-2xl p-3 text-sm hover:neon-border transition-shadow cursor-pointer"
              >
                {t}
              </div>
            ))}
          </div>
        </div>
      </div>
    </PageWrapper>
  );
}
