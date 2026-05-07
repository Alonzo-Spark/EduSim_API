import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { PageWrapper } from "@/components/Card";
import { Crumbs } from "@/components/Crumbs";
import {
  CanvasGame,
  type LiveStats,
  type Sample,
} from "@/simulations/projectile-motion/CanvasGame";
import { Controls } from "@/simulations/projectile-motion/Controls";
import { HUD } from "@/simulations/projectile-motion/HUD";
import { GraphPanel } from "@/simulations/projectile-motion/GraphPanel";
import {
  GRAVITIES,
  type GravityKey,
  type ProjectileType,
  type SimulationMode,
} from "@/simulations/projectile-motion/physics";
import { Target, X } from "lucide-react";

export const Route = createFileRoute("/simulation/class9/physics/laws-of-motion/projectile-motion")(
  { component: ProjectileSim },
);

function ProjectileSim() {
  // Core state
  const [gravityKey, setGravityKey] = useState<GravityKey>("Earth");
  const [gravityValue, setGravityValue] = useState(GRAVITIES.Earth);
  const [stats, setStats] = useState<LiveStats>({
    power: 0,
    angle: 0,
    range: 0,
    height: 0,
    tof: 0,
    impactSpeed: 0,
  });
  const [samples, setSamples] = useState<Sample[]>([]);
  const [hits, setHits] = useState(0);

  // Mode and input state
  const [mode, setMode] = useState<SimulationMode>("slingshot");
  const [projectileType, setProjectileType] = useState<ProjectileType>("bird");
  const [manualPower, setManualPower] = useState(30);
  const [manualAngle, setManualAngle] = useState(45);

  // Trigger counters
  const [launchTick, setLaunchTick] = useState(0);
  const [resetTick, setResetTick] = useState(0);
  const [replayTick, setReplayTick] = useState(0);
  const [explainOpen, setExplainOpen] = useState(false);

  // Slingshot drag state (for display when in slingshot mode)
  const [drag, setDrag] = useState({ power: 0, angle: 45 });

  const power = mode === "slingshot" ? drag.power : manualPower;
  const angle = mode === "slingshot" ? drag.angle : manualAngle;

  function handleModeChange(next: SimulationMode) {
    setMode(next);
    setLaunchTick(0);
    setReplayTick(0);
    setDrag({ power: 0, angle: 45 });
    setStats({ power: 0, angle: 0, range: 0, height: 0, tof: 0, impactSpeed: 0 });
    setSamples([]);
  }

  function handleLaunch() {
    if (mode !== "manual" || manualPower <= 0) return;
    setLaunchTick((n) => n + 1);
  }

  const hudStats = [
    { label: "Range R", value: stats.range.toFixed(1), unit: "m", color: "#a78bfa" },
    { label: "Max Height H", value: stats.height.toFixed(1), unit: "m", color: "#7dd3fc" },
    { label: "Time of Flight T", value: stats.tof.toFixed(2), unit: "s", color: "#f0abfc" },
    { label: "Impact Speed", value: stats.impactSpeed.toFixed(1), unit: "m/s", color: "#fda4af" },
  ];

  return (
    <PageWrapper>
      <Crumbs
        items={[
          { label: "Home", to: "/" },
          { label: "Class 9", to: "/subjects/$classId", params: { classId: "9" } },
          {
            label: "Physics",
            to: "/chapters/$classId/$subject",
            params: { classId: "9", subject: "physics" },
          },
          { label: "Laws of Motion" },
          { label: "Projectile Motion" },
        ]}
      />

      <div className="flex items-center justify-between flex-wrap gap-3 mb-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-gradient">Projectile Motion · Lab</h1>
          <p className="text-sm text-muted-foreground">
            {mode === "slingshot"
              ? "Drag the projectile, aim at targets, learn the physics."
              : "Input velocity and angle to understand projectile motion."}
          </p>
        </div>
        <div className="glass rounded-2xl px-4 py-2 flex items-center gap-2">
          <Target className="w-4 h-4 text-[var(--neon-cyan)]" />
          <span className="text-sm">
            Targets hit: <span className="font-mono font-bold text-[var(--neon-cyan)]">{hits}</span>
          </span>
        </div>
      </div>

      <HUD stats={hudStats} />

      <div className="grid lg:grid-cols-[280px_1fr] gap-4 mt-4">
        <Controls
          mode={mode}
          setMode={handleModeChange}
          projectileType={projectileType}
          setProjectileType={setProjectileType}
          power={power}
          angle={angle}
          manualPower={manualPower}
          setManualPower={setManualPower}
          manualAngle={manualAngle}
          setManualAngle={setManualAngle}
          gravityKey={gravityKey}
          setGravityKey={setGravityKey}
          gravityValue={gravityValue}
          setGravityValue={setGravityValue}
          onLaunch={handleLaunch}
          onReset={() => setResetTick((n) => n + 1)}
          onReplay={() => setReplayTick((n) => n + 1)}
          onExplain={() => setExplainOpen(true)}
          canLaunch={mode === "manual" && manualPower > 0}
        />

        <div className="glass-strong rounded-3xl p-3 overflow-hidden">
          <CanvasGame
            gravityKey={gravityKey}
            gravityValue={gravityValue}
            projectileType={projectileType}
            mode={mode}
            manualPower={manualPower}
            manualAngle={manualAngle}
            onStats={setStats}
            onSamples={setSamples}
            onHit={setHits}
            launchTrigger={launchTick}
            resetTrigger={resetTick}
            replayTrigger={replayTick}
            onPowerAngle={(p, a) => setDrag({ power: p, angle: a })}
          />
        </div>
      </div>

      <div className="mt-4">
        <GraphPanel samples={samples} T={Math.max(stats.tof, 0.5)} />
      </div>

      <AnimatePresence>
        {explainOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4"
            onClick={() => setExplainOpen(false)}
          >
            <motion.div
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              onClick={(e) => e.stopPropagation()}
              className="glass-strong rounded-3xl p-6 max-w-lg w-full neon-border relative"
            >
              <button
                onClick={() => setExplainOpen(false)}
                className="absolute top-4 right-4 glass rounded-full p-1.5"
              >
                <X className="w-4 h-4" />
              </button>
              <h2 className="text-xl font-bold text-gradient mb-3">
                Why is the trajectory parabolic?
              </h2>
              <div className="space-y-3 text-sm text-muted-foreground">
                <p>
                  Once released, the only force acting on the projectile (ignoring drag) is gravity,
                  pulling it straight down at{" "}
                  <span className="text-[var(--neon-cyan)] font-mono">
                    {gravityValue.toFixed(1)}
                  </span>{" "}
                  m/s².
                </p>
                <p>
                  By <strong className="text-foreground">Newton's First Law</strong>, the horizontal
                  velocity stays constant. By the
                  <strong className="text-foreground"> Second Law</strong>, the vertical velocity
                  changes linearly with time. Combine them and position becomes a quadratic in{" "}
                  <em>t</em> — that's the parabola you see.
                </p>
                <p>
                  Switch planets to feel how a smaller <em>g</em> stretches the curve and a larger{" "}
                  <em>g</em> crushes it. Try different modes and projectile types to explore!
                </p>
              </div>
              <Link
                to="/"
                className="inline-block mt-4 text-xs text-[var(--neon-cyan)] hover:underline"
              >
                ← Back to dashboard
              </Link>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </PageWrapper>
  );
}
