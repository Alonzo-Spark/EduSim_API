import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Play, RotateCcw, Repeat, Lightbulb } from "lucide-react";
import {
  GRAVITIES,
  PROJECTILE_STYLES,
  clampGravity,
  type GravityKey,
  type ProjectileType,
  type SimulationMode,
} from "./physics";

type Props = {
  mode: SimulationMode;
  setMode: (m: SimulationMode) => void;
  projectileType: ProjectileType;
  setProjectileType: (t: ProjectileType) => void;
  power: number;
  angle: number;
  manualPower: number;
  setManualPower: (p: number) => void;
  manualAngle: number;
  setManualAngle: (a: number) => void;
  gravityKey: GravityKey;
  setGravityKey: (k: GravityKey) => void;
  gravityValue: number;
  setGravityValue: (g: number) => void;
  onLaunch: () => void;
  onReset: () => void;
  onReplay: () => void;
  onExplain: () => void;
  canLaunch: boolean;
};

export function Controls({
  mode,
  setMode,
  projectileType,
  setProjectileType,
  power,
  angle,
  manualPower,
  setManualPower,
  manualAngle,
  setManualAngle,
  gravityKey,
  setGravityKey,
  gravityValue,
  setGravityValue,
  onLaunch,
  onReset,
  onReplay,
  onExplain,
  canLaunch,
}: Props) {
  const g = GRAVITIES[gravityKey];
  const [localManualPower, setLocalManualPower] = useState(manualPower.toString());
  const [localManualAngle, setLocalManualAngle] = useState(manualAngle.toString());

  useEffect(() => {
    setLocalManualPower(manualPower.toString());
  }, [manualPower]);

  useEffect(() => {
    setLocalManualAngle(manualAngle.toString());
  }, [manualAngle]);

  const displayPower = mode === "slingshot" ? power : manualPower;
  const displayAngle = mode === "slingshot" ? angle : manualAngle;

  return (
    <div className="glass-strong rounded-3xl p-5 space-y-5 h-full overflow-y-auto">
      <div>
        <h3 className="text-sm font-bold uppercase tracking-widest text-muted-foreground mb-3">
          Simulation Mode
        </h3>
        <div className="grid grid-cols-2 gap-2">
          {(["slingshot", "manual"] as const).map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={`px-3 py-2 rounded-xl text-xs font-medium transition-all capitalize ${
                mode === m
                  ? "bg-gradient-to-br from-[var(--neon-purple)] to-[var(--neon-blue)] text-white glow-purple"
                  : "glass hover:neon-border"
              }`}
            >
              {m === "slingshot" ? "🎯 Drag" : "⌨️ Input"}
            </button>
          ))}
        </div>
      </div>

      <div>
        <h3 className="text-sm font-bold uppercase tracking-widest text-muted-foreground mb-2">
          Projectile
        </h3>
        <div className="grid grid-cols-3 gap-2">
          {(Object.keys(PROJECTILE_STYLES) as ProjectileType[]).map((type) => (
            <button
              key={type}
              onClick={() => setProjectileType(type)}
              className={`px-2 py-2 rounded-xl text-xs font-medium transition-all ${
                projectileType === type
                  ? "bg-gradient-to-br from-[var(--neon-cyan)] to-[var(--neon-blue)] text-white glow-cyan"
                  : "glass hover:neon-border"
              }`}
              title={PROJECTILE_STYLES[type].label}
            >
              {type === "ball" && "⚽"}
              {type === "bird" && "🐦"}
              {type === "square" && "⬜"}
            </button>
          ))}
        </div>
      </div>

      {mode === "manual" && (
        <div className="glass rounded-2xl p-3 space-y-3">
          <h3 className="text-xs font-bold uppercase tracking-widest text-muted-foreground">
            Launch Parameters
          </h3>

          <div>
            <label className="text-xs text-muted-foreground block mb-2 flex items-center justify-between gap-2">
              <span>Initial Velocity</span>
              <span className="font-mono text-[var(--neon-purple)]">
                {manualPower.toFixed(1)} m/s
              </span>
            </label>
            <input
              type="range"
              min="0"
              max="100"
              step="0.25"
              value={localManualPower}
              onChange={(e) => {
                setLocalManualPower(e.target.value);
                setManualPower(parseFloat(e.target.value));
              }}
              className="w-full h-2 bg-gradient-to-r from-[var(--neon-purple)] to-[var(--neon-blue)] rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex gap-2 mt-2">
              <input
                type="number"
                min="0"
                max="100"
                step="0.1"
                value={localManualPower}
                onChange={(e) => {
                  setLocalManualPower(e.target.value);
                  setManualPower(Math.min(100, Math.max(0, parseFloat(e.target.value) || 0)));
                }}
                className="flex-1 px-2 py-1 text-xs bg-black/30 border border-[var(--neon-purple)]/50 rounded text-white focus:outline-none focus:border-[var(--neon-purple)]"
              />
              <span className="text-xs text-muted-foreground px-2 py-1">m/s</span>
            </div>
          </div>

          <div>
            <label className="text-xs text-muted-foreground block mb-2 flex items-center justify-between gap-2">
              <span>Launch Angle</span>
              <span className="font-mono text-[var(--neon-cyan)]">{manualAngle.toFixed(1)}°</span>
            </label>
            <input
              type="range"
              min="0"
              max="90"
              step="0.25"
              value={localManualAngle}
              onChange={(e) => {
                setLocalManualAngle(e.target.value);
                setManualAngle(parseFloat(e.target.value));
              }}
              className="w-full h-2 bg-gradient-to-r from-[var(--neon-cyan)] to-[var(--neon-blue)] rounded-lg appearance-none cursor-pointer"
            />
            <div className="flex gap-2 mt-2">
              <input
                type="number"
                min="0"
                max="90"
                step="0.1"
                value={localManualAngle}
                onChange={(e) => {
                  setLocalManualAngle(e.target.value);
                  setManualAngle(Math.min(90, Math.max(0, parseFloat(e.target.value) || 0)));
                }}
                className="flex-1 px-2 py-1 text-xs bg-black/30 border border-[var(--neon-cyan)]/50 rounded text-white focus:outline-none focus:border-[var(--neon-cyan)]"
              />
              <span className="text-xs text-muted-foreground px-2 py-1">°</span>
            </div>
          </div>
        </div>
      )}

      <div>
        <h3 className="text-sm font-bold uppercase tracking-widest text-muted-foreground mb-3">
          Current Values
        </h3>
        <div className="space-y-3">
          <Readout
            label="Power"
            value={displayPower.toFixed(1)}
            unit="m/s"
            color="var(--neon-purple)"
          />
          <Readout
            label="Angle θ"
            value={displayAngle.toFixed(1)}
            unit="°"
            color="var(--neon-cyan)"
          />
          <Readout label="Gravity" value={g.toFixed(1)} unit="m/s²" color="var(--neon-blue)" />
        </div>
      </div>

      <div className="glass rounded-2xl p-3 space-y-3">
        <div className="flex items-center justify-between gap-2">
          <h3 className="text-sm font-bold uppercase tracking-widest text-muted-foreground">
            Gravity
          </h3>
          <span className="font-mono text-xs text-[var(--neon-blue)]">
            {gravityValue.toFixed(1)} m/s²
          </span>
        </div>
        <input
          type="range"
          min="1"
          max="25"
          step="0.1"
          value={gravityValue}
          onChange={(e) => {
            const next = clampGravity(parseFloat(e.target.value) || 1);
            setGravityValue(next);
            if (Math.abs(next - GRAVITIES.Earth) < 0.15) setGravityKey("Earth");
            else if (Math.abs(next - GRAVITIES.Moon) < 0.15) setGravityKey("Moon");
            else if (Math.abs(next - GRAVITIES.Mars) < 0.15) setGravityKey("Mars");
          }}
          className="w-full h-2 bg-gradient-to-r from-[var(--neon-cyan)] to-[var(--neon-purple)] rounded-lg appearance-none cursor-pointer"
        />
        <div className="grid grid-cols-3 gap-2">
          {(Object.keys(GRAVITIES) as GravityKey[]).map((k) => (
            <button
              key={k}
              onClick={() => {
                setGravityKey(k);
                setGravityValue(GRAVITIES[k]);
              }}
              className={`px-2 py-2 rounded-xl text-xs font-medium transition-all ${
                gravityKey === k
                  ? "bg-gradient-to-br from-[var(--neon-purple)] to-[var(--neon-blue)] text-white glow-purple"
                  : "glass hover:neon-border"
              }`}
            >
              {k}
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-2 pt-2 border-t border-white/10">
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.97 }}
          onClick={onLaunch}
          disabled={!canLaunch}
          className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-2xl bg-gradient-to-r from-[var(--neon-purple)] to-[var(--neon-blue)] text-white font-medium hover:glow-purple transition-all disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <Play className="w-4 h-4" /> Launch
        </motion.button>

        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={onReset}
            className="flex items-center justify-center gap-1 px-3 py-2 rounded-2xl glass text-sm hover:neon-border transition-all"
          >
            <RotateCcw className="w-3.5 h-3.5" /> Reset
          </button>
          <button
            onClick={onReplay}
            className="flex items-center justify-center gap-1 px-3 py-2 rounded-2xl glass text-sm hover:neon-border transition-all"
          >
            <Repeat className="w-3.5 h-3.5" /> Replay
          </button>
        </div>

        <button
          onClick={onExplain}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-2xl glass text-sm hover:neon-border transition-all"
        >
          <Lightbulb className="w-3.5 h-3.5" /> Physics
        </button>
      </div>

      <div className="glass rounded-2xl p-3 text-xs text-muted-foreground space-y-2">
        <p className="font-semibold text-foreground">Kinematic Equations:</p>
        <div className="font-mono space-y-1">
          <p>R = v² sin(2θ) / g</p>
          <p>H = v² sin²(θ) / 2g</p>
          <p>T = 2v sin(θ) / g</p>
        </div>
      </div>
    </div>
  );
}

function Readout({
  label,
  value,
  unit,
  color,
}: {
  label: string;
  value: string;
  unit: string;
  color: string;
}) {
  return (
    <div className="glass rounded-xl p-2 flex justify-between items-center">
      <span className="text-xs text-muted-foreground">{label}</span>
      <div className="flex items-baseline gap-1">
        <span className="font-mono font-bold text-sm" style={{ color }}>
          {value}
        </span>
        <span className="text-xs text-muted-foreground">{unit}</span>
      </div>
    </div>
  );
}
