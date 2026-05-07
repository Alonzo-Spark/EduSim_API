import { createFileRoute } from "@tanstack/react-router";
import { useCallback, useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Hand, Zap, Rocket, X, CircleStop, Sparkles } from "lucide-react";
import { PageWrapper } from "@/components/Card";
import { Crumbs } from "@/components/Crumbs";
import { HUD } from "@/components/sim/HUD";
import { LawControls } from "@/components/sim/laws/LawControls";
import { LawGraphPanel } from "@/components/sim/laws/LawGraphPanel";
import { FirstLawCanvas } from "@/components/sim/laws/FirstLawCanvas";
import { SecondLawCanvas } from "@/components/sim/laws/SecondLawCanvas";
import { ThirdLawCanvas } from "@/components/sim/laws/ThirdLawCanvas";
import type { LawSample } from "@/components/sim/laws/types";
import { physicsSimulationApi } from "@/services/physicsSimulationApi";

export const Route = createFileRoute("/simulation/class9/physics/laws-of-motion")({
  component: LawsOfMotionLab,
});

type Tab = "first" | "second" | "third";

const TABS: { id: Tab; label: string; icon: typeof Hand }[] = [
  { id: "first", label: "First Law", icon: Hand },
  { id: "second", label: "Second Law", icon: Zap },
  { id: "third", label: "Third Law", icon: Rocket },
];

function LawsOfMotionLab() {
  const [tab, setTab] = useState<Tab>("first");
  const [explainOpen, setExplainOpen] = useState(false);

  return (
    <PageWrapper>
      <Crumbs
        items={[
          { label: "Home", to: "/" },
          { label: "Class 9", to: "/subjects/$classId", params: { classId: "9" } },
          { label: "Physics", to: "/chapters/$classId/$subject", params: { classId: "9", subject: "physics" } },
          { label: "Laws of Motion" },
        ]}
      />

      <div className="flex items-center justify-between flex-wrap gap-3 mb-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-gradient">Newton's Laws of Motion · Lab</h1>
          <p className="text-sm text-muted-foreground">Three interactive simulations to feel inertia, force, and reaction.</p>
        </div>
        <div className="glass rounded-2xl p-1 flex gap-1">
          {TABS.map((t) => {
            const Icon = t.icon;
            const active = tab === t.id;
            return (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                  active
                    ? "bg-gradient-to-r from-[var(--neon-purple)] to-[var(--neon-blue)] text-white glow-purple"
                    : "hover:bg-white/5 text-muted-foreground"
                }`}
              >
                <Icon className="w-4 h-4" /> {t.label}
              </button>
            );
          })}
        </div>
      </div>

      {tab === "first" && <FirstLawTab onExplain={() => setExplainOpen(true)} />}
      {tab === "second" && <SecondLawTab onExplain={() => setExplainOpen(true)} />}
      {tab === "third" && <ThirdLawTab onExplain={() => setExplainOpen(true)} />}

      <AnimatePresence>
        {explainOpen && (
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4"
            onClick={() => setExplainOpen(false)}
          >
            <motion.div
              initial={{ scale: 0.9, y: 20 }} animate={{ scale: 1, y: 0 }} exit={{ scale: 0.9, y: 20 }}
              onClick={(e) => e.stopPropagation()}
              className="glass-strong rounded-3xl p-6 max-w-lg w-full neon-border relative"
            >
              <button onClick={() => setExplainOpen(false)} className="absolute top-4 right-4 glass rounded-full p-1.5">
                <X className="w-4 h-4" />
              </button>
              <ExplainContent tab={tab} />
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </PageWrapper>
  );
}

/* ── First Law Tab ────────────────────────────────────────────────────────── */

function FirstLawTab({ onExplain }: { onExplain: () => void }) {
  const [mass, setMass] = useState(5);
  const [friction, setFriction] = useState(0.2);
  const [velocity, setVelocity] = useState(8);
  const [showVectors, setShowVectors] = useState(true);
  const [running, setRunning] = useState(false);
  const [brakeTrigger, setBrakeTrigger] = useState(0);
  const [resetTrigger, setResetTrigger] = useState(0);
  const [samples, setSamples] = useState<LawSample[]>([]);
  const [live, setLive] = useState({ busV: 0, objV: 0, netF: 0, inertia: 0 });

  const onSamples = useCallback((s: LawSample[]) => setSamples(s), []);
  const onLive = useCallback((d: typeof live) => setLive(d), []);

  return (
    <>
      <HUD stats={[
        { label: "Bus Velocity", value: live.busV.toFixed(1), unit: "m/s", color: "#a78bfa" },
        { label: "Object Velocity", value: live.objV.toFixed(1), unit: "m/s", color: "#7dd3fc" },
        { label: "Net Force", value: live.netF.toFixed(1), unit: "N", color: "#f0abfc" },
        { label: "Inertia (p)", value: live.inertia.toFixed(1), unit: "kg·m/s", color: "#fda4af" },
      ]} />

      <div className="grid lg:grid-cols-[280px_1fr] gap-4 mt-4">
        <LawControls
          title="Inertia Parameters"
          sliders={[
            { label: "Mass", value: mass, min: 1, max: 20, unit: "kg", color: "#a78bfa", onChange: setMass },
            { label: "Friction μ", value: friction, min: 0, max: 1, step: 0.05, unit: "", color: "#7dd3fc", onChange: setFriction },
            { label: "Initial Velocity", value: velocity, min: 0, max: 20, unit: "m/s", color: "#f0abfc", onChange: setVelocity },
          ]}
          formulaTitle="Newton's First Law"
          formula="ΣF = 0  ⇒  Δv = 0"
          liveEquation="An object in motion stays in motion."
          showVectors={showVectors} setShowVectors={setShowVectors}
          running={running} onPlay={() => setRunning(true)} onPause={() => setRunning(false)}
          onReset={() => { setResetTrigger((n) => n + 1); setRunning(false); }}
          onAction={{ label: "Brake!", icon: <CircleStop className="w-4 h-4" />, onClick: () => setBrakeTrigger((n) => n + 1) }}
          onExplain={onExplain}
        />
        <div className="glass-strong rounded-3xl p-3 overflow-hidden min-h-[400px]">
          <FirstLawCanvas
            mass={mass} friction={friction} velocity={velocity}
            showVectors={showVectors} running={running}
            brakeTrigger={brakeTrigger} resetTrigger={resetTrigger}
            onSamples={onSamples} onLive={onLive}
          />
        </div>
      </div>

      <div className="mt-4">
        <LawGraphPanel samples={samples} series={[
          { title: "Velocity vs t", color: "#7dd3fc", unit: "m/s", get: (s) => s.v },
          { title: "Acceleration vs t", color: "#a78bfa", unit: "m/s²", get: (s) => s.a },
          { title: "Position vs t", color: "#f0abfc", unit: "m", get: (s) => s.x },
        ]} />
      </div>
    </>
  );
}

/* ── Second Law Tab ───────────────────────────────────────────────────────── */

function SecondLawTab({ onExplain }: { onExplain: () => void }) {
  const [force, setForce] = useState(20);
  const [mass, setMass] = useState(5);
  const [showVectors, setShowVectors] = useState(true);
  const [running, setRunning] = useState(false);
  const [resetTrigger, setResetTrigger] = useState(0);
  
  // Real-time canvas samples & live stats
  const [canvasSamples, setCanvasSamples] = useState<LawSample[]>([]);
  const [live, setLive] = useState({ force: 20, mass: 5, accel: 4, velocity: 0, displacement: 0 });

  // Backend API data
  const [loading, setLoading] = useState(false);
  const [apiTrajectory, setApiTrajectory] = useState<LawSample[] | null>(null);

  const onSamples = useCallback((s: LawSample[]) => setCanvasSamples(s), []);
  const onLive = useCallback((d: typeof live) => setLive(d), []);

  // Fetch backend simulation on parameter change
  useEffect(() => {
    let active = true;
    const fetchSim = async () => {
      setLoading(true);
      const res = await physicsSimulationApi.simulateMomentum(mass, force);
      if (active && res.success && res.data) {
        setApiTrajectory(res.data.trajectory as LawSample[]);
      }
      if (active) setLoading(false);
    };
    const timer = setTimeout(fetchSim, 300);
    return () => { active = false; clearTimeout(timer); };
  }, [force, mass]);

  const a = force / Math.max(0.1, mass);

  return (
    <>
      <HUD stats={[
        { label: "Force", value: force.toFixed(0), unit: "N", color: "#ff6ad8" },
        { label: "Mass", value: mass.toFixed(0), unit: "kg", color: "#a78bfa" },
        { label: "Acceleration (Backend)", value: a.toFixed(2), unit: "m/s²", color: "#7dd3fc" },
        { label: "Velocity", value: live.velocity.toFixed(1), unit: "m/s", color: "#fda4af" },
      ]} />

      <div className="grid lg:grid-cols-[280px_1fr] gap-4 mt-4">
        <LawControls
          title="Force & Mass"
          sliders={[
            { label: "Applied Force", value: force, min: 0, max: 50, unit: "N", color: "#ff6ad8", onChange: setForce },
            { label: "Mass", value: mass, min: 1, max: 20, unit: "kg", color: "#a78bfa", onChange: setMass },
          ]}
          formulaTitle="Newton's Second Law"
          formula="F = m × a"
          liveEquation={`${force} N = ${mass} kg × ${a.toFixed(2)} m/s²`}
          showVectors={showVectors} setShowVectors={setShowVectors}
          running={running} onPlay={() => setRunning(true)} onPause={() => setRunning(false)}
          onReset={() => { setResetTrigger((n) => n + 1); setRunning(false); }}
          onExplain={onExplain}
        />
        <div className="glass-strong rounded-3xl p-3 overflow-hidden min-h-[400px] relative">
          {loading && (
            <div className="absolute top-4 right-4 z-10 glass px-3 py-1 rounded-full text-xs text-muted-foreground flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-[var(--neon-purple)] animate-ping" />
              Computing Trajectory...
            </div>
          )}
          <SecondLawCanvas
            force={force} mass={mass}
            showVectors={showVectors} running={running}
            resetTrigger={resetTrigger}
            onSamples={onSamples} onLive={onLive}
          />
        </div>
      </div>

      <div className="mt-4">
        {/* We use the backend trajectory if available, falling back to canvas samples */}
        <LawGraphPanel samples={apiTrajectory || canvasSamples} series={[
          { title: "Velocity vs t", color: "#7dd3fc", unit: "m/s", get: (s) => s.v },
          { title: "Acceleration vs t", color: "#a78bfa", unit: "m/s²", get: (s) => s.a },
          { title: "Force vs t", color: "#ff6ad8", unit: "N", get: (s) => s.f },
        ]} />
      </div>
    </>
  );
}

/* ── Third Law Tab ────────────────────────────────────────────────────────── */

function ThirdLawTab({ onExplain }: { onExplain: () => void }) {
  const [thrust, setThrust] = useState(20);
  const [massA, setMassA] = useState(5);
  const [massB, setMassB] = useState(5);
  const [showVectors, setShowVectors] = useState(true);
  const [running, setRunning] = useState(false);
  const [launchTrigger, setLaunchTrigger] = useState(0);
  const [resetTrigger, setResetTrigger] = useState(0);
  
  const [canvasSamples, setCanvasSamples] = useState<LawSample[]>([]);
  const [live, setLive] = useState({ thrust: 20, reaction: 20, momentum: 0, vA: 0, vB: 0 });

  const [loading, setLoading] = useState(false);
  const [apiTrajectory, setApiTrajectory] = useState<LawSample[] | null>(null);

  const onSamples = useCallback((s: LawSample[]) => setCanvasSamples(s), []);
  const onLive = useCallback((d: typeof live) => setLive(d), []);

  useEffect(() => {
    if (launchTrigger === 0) {
      setApiTrajectory(null);
      return;
    }
    let active = true;
    const fetchSim = async () => {
      setLoading(true);
      const res = await physicsSimulationApi.simulateActionReaction(massA, massB, thrust);
      if (active && res.success && res.data) {
        // Map ActionReactionData to LawSample[] for the graph
        const mapped: LawSample[] = res.data.trajectories.object2.map((pt, i) => {
          const t = pt.t;
          const x = pt.position;
          // Calculate velocity approximately or strictly from backend if it returned it
          // The backend currently only returns `position`. We can approximate v=dx/dt
          // But since v = a*t, and a = res.data.acceleration2
          const a = res.data!.acceleration2;
          const v = a * t;
          return { t, x, v, a, f: thrust };
        });
        setApiTrajectory(mapped);
      }
      if (active) setLoading(false);
    };
    fetchSim();
    return () => { active = false; };
  }, [launchTrigger, massA, massB, thrust]);

  return (
    <>
      <HUD stats={[
        { label: "Thrust (Action)", value: live.thrust.toFixed(0), unit: "N", color: "#f0abfc" },
        { label: "Reaction", value: live.reaction.toFixed(0), unit: "N", color: "#7dd3fc" },
        { label: "Momentum |p|", value: live.momentum.toFixed(1), unit: "kg·m/s", color: "#a78bfa" },
        { label: "Velocity B", value: live.vB.toFixed(1), unit: "m/s", color: "#fda4af" },
      ]} />

      <div className="grid lg:grid-cols-[280px_1fr] gap-4 mt-4">
        <LawControls
          title="Action–Reaction"
          sliders={[
            { label: "Thrust Force", value: thrust, min: 5, max: 50, unit: "N", color: "#ff6ad8", onChange: setThrust },
            { label: "Mass A", value: massA, min: 1, max: 20, unit: "kg", color: "#7dd3fc", onChange: setMassA },
            { label: "Mass B", value: massB, min: 1, max: 20, unit: "kg", color: "#f0abfc", onChange: setMassB },
          ]}
          formulaTitle="Newton's Third Law"
          formula="F_AB = − F_BA"
          liveEquation={`vA = ${live.vA.toFixed(2)} m/s · vB = ${live.vB.toFixed(2)} m/s`}
          showVectors={showVectors} setShowVectors={setShowVectors}
          running={running} onPlay={() => setRunning(true)} onPause={() => setRunning(false)}
          onReset={() => { setResetTrigger((n) => n + 1); setLaunchTrigger(0); setRunning(false); }}
          onAction={{ label: "Launch", icon: <Rocket className="w-4 h-4" />, onClick: () => { setLaunchTrigger((n) => n + 1); setRunning(true); } }}
          onExplain={onExplain}
        />
        <div className="glass-strong rounded-3xl p-3 overflow-hidden min-h-[400px] relative">
          {loading && (
            <div className="absolute top-4 right-4 z-10 glass px-3 py-1 rounded-full text-xs text-muted-foreground flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-[var(--neon-purple)] animate-ping" />
              Fetching Results...
            </div>
          )}
          <ThirdLawCanvas
            thrust={thrust} massA={massA} massB={massB}
            showVectors={showVectors} running={running}
            launchTrigger={launchTrigger} resetTrigger={resetTrigger}
            onSamples={onSamples} onLive={onLive}
          />
        </div>
      </div>

      <div className="mt-4">
        <LawGraphPanel samples={apiTrajectory || canvasSamples} series={[
          { title: "Velocity B vs t", color: "#7dd3fc", unit: "m/s", get: (s) => s.v },
          { title: "Position B vs t", color: "#f0abfc", unit: "m", get: (s) => s.x },
          { title: "Force vs t", color: "#ff6ad8", unit: "N", get: (s) => s.f },
        ]} />
      </div>
    </>
  );
}

/* ── Explain Modal Content ────────────────────────────────────────────────── */

function ExplainContent({ tab }: { tab: Tab }) {
  const [aiPrompt, setAiPrompt] = useState("");
  const [aiResponse, setAiResponse] = useState("");
  const [isAiLoading, setIsAiLoading] = useState(false);

  useEffect(() => {
    if (tab === "first") setAiPrompt("Explain inertia and Newton's First Law");
    else if (tab === "second") setAiPrompt("Explain Momentum and Newton's Second Law");
    else setAiPrompt("Explain Action and Reaction in Newton's Third Law");
  }, [tab]);

  const handleAskAi = async () => {
    if (!aiPrompt.trim() || isAiLoading) return;
    setIsAiLoading(true);
    const res = await physicsSimulationApi.queryRag(aiPrompt);
    if (res.success && res.data) {
      setAiResponse(res.data.answer);
    } else {
      setAiResponse(`Error: ${res.error}`);
    }
    setIsAiLoading(false);
  };

  return (
    <div className="flex flex-col h-full max-h-[80vh]">
      <div className="shrink-0">
        {tab === "first" && (
          <>
            <h2 className="text-xl font-bold text-gradient mb-3">First Law — Inertia</h2>
            <div className="space-y-2 text-sm text-muted-foreground">
              <p>An object continues in its state of rest or uniform motion unless acted upon by an external force. When the bus brakes suddenly, the object on top has no horizontal force acting on it instantly, so it keeps moving forward.</p>
              <p>Friction (μ) is what eventually slows the sliding object down. Heavier objects (more mass) carry more <em>momentum</em> and resist change more strongly.</p>
            </div>
          </>
        )}
        {tab === "second" && (
          <>
            <h2 className="text-xl font-bold text-gradient mb-3">Second Law — F = ma</h2>
            <div className="space-y-2 text-sm text-muted-foreground">
              <p>The acceleration of an object is directly proportional to the net force applied and inversely proportional to its mass.</p>
              <p>Try doubling the force — acceleration doubles. Double the mass and acceleration halves. The pink arrow shows force, blue shows acceleration, red shows current velocity.</p>
            </div>
          </>
        )}
        {tab === "third" && (
          <>
            <h2 className="text-xl font-bold text-gradient mb-3">Third Law — Action &amp; Reaction</h2>
            <div className="space-y-2 text-sm text-muted-foreground">
              <p>For every action there is an equal and opposite reaction. When object A pushes B, B pushes A back with the same force in the opposite direction.</p>
              <p>Even though forces are equal, accelerations are not — the lighter object accelerates more (a = F/m). This is why a rocket's tiny exhaust mass moving fast can push a huge rocket forward.</p>
            </div>
          </>
        )}
      </div>

      <hr className="border-white/10 my-4" />

      <div className="flex-1 flex flex-col min-h-[250px]">
        <h3 className="text-sm font-bold uppercase tracking-widest text-muted-foreground mb-3 flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-[var(--neon-cyan)]" /> Ask AI Textbook
        </h3>
        <div className="flex gap-2 mb-3">
          <input 
            type="text" 
            value={aiPrompt}
            onChange={(e) => setAiPrompt(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleAskAi()}
            placeholder="Ask a textbook question..."
            className="flex-1 bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-[var(--neon-cyan)] transition-colors text-white"
          />
          <button 
            onClick={handleAskAi}
            disabled={isAiLoading || !aiPrompt.trim()}
            className="px-4 py-2 bg-[var(--neon-cyan)]/20 text-[var(--neon-cyan)] rounded-xl text-sm font-medium hover:bg-[var(--neon-cyan)]/30 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isAiLoading ? "Thinking..." : "Ask AI"}
          </button>
        </div>

        <div className="flex-1 bg-[#020617] border border-white/10 rounded-xl p-3 overflow-y-auto text-sm text-muted-foreground max-h-[300px]">
          {isAiLoading ? (
             <div className="flex justify-center items-center h-full min-h-[100px]">
               <span className="w-5 h-5 rounded-full border-2 border-[var(--neon-cyan)] border-t-transparent animate-spin" />
             </div>
          ) : aiResponse ? (
             <div className="whitespace-pre-wrap leading-relaxed">{aiResponse}</div>
          ) : (
             <div className="flex h-full min-h-[100px] items-center justify-center text-white/20 italic">
               RAG AI responses will appear here...
             </div>
          )}
        </div>
      </div>
    </div>
  );
}
