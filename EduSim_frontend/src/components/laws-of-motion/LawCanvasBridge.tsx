import { useCallback, useEffect, useMemo, useRef } from "react";
import type { LawSimulationConfig } from "@/types/lawsOfMotion";
import { LawCanvasStage } from "./LawCanvasStage";
import { createLawEngine } from "@/simulations/laws-of-motion/engines";

interface LawCanvasBridgeProps {
  config: LawSimulationConfig;
  onSnapshot?: (snapshot: unknown) => void;
  onEngineReady?: (engine: ReturnType<typeof createLawEngine>) => void;
  className?: string;
}

/**
 * Stable bridge between the React state world and the canvas engine.
 *
 * Key stabilisation:
 * - Engine is created once via useRef (not useMemo with config dep)
 *   so config object identity changes never recreate it.
 * - onSnapshot is throttled to 15 FPS via useRef + timestamp guard so
 *   it cannot trigger 60 React renders per second.
 * - onEngineReady fires only once (on mount) via a ref guard.
 */
export function LawCanvasBridge({
  config,
  onSnapshot,
  onEngineReady,
  className,
}: LawCanvasBridgeProps) {
  // Create the engine ONCE regardless of config changes.
  // Updates to config are pushed imperatively via loadConfig() below.
  const engineRef = useRef<ReturnType<typeof createLawEngine> | null>(null);
  if (engineRef.current === null) {
    engineRef.current = createLawEngine(config);
  }
  const engine = engineRef.current;

  // Notify the parent of the engine instance exactly once.
  const readyFiredRef = useRef(false);
  useEffect(() => {
    if (!readyFiredRef.current) {
      readyFiredRef.current = true;
      onEngineReady?.(engine);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Push config changes into the engine imperatively – no recreation.
  const configRef = useRef(config);
  useEffect(() => {
    if (configRef.current !== config) {
      configRef.current = config;
      engine.loadConfig(config);
      engine.setControls(config.controls);
    }
  }, [config, engine]);

  // Throttle snapshot callbacks to ~15 FPS to prevent 60 React
  // re-renders per second.  Physics still runs at 60 FPS on the canvas.
  const lastSnapshotTime = useRef(0);
  const onSnapshotRef = useRef(onSnapshot);
  onSnapshotRef.current = onSnapshot;

  const onFrame = useCallback(() => {
    const now = performance.now();
    if (now - lastSnapshotTime.current < 66) return; // ≈15 FPS cap
    lastSnapshotTime.current = now;
    onSnapshotRef.current?.(engine.getSnapshot());
  }, [engine]);

  return <LawCanvasStage engine={engine} className={className} onFrame={onFrame} />;
}
