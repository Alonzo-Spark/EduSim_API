/**
 * Simulation Canvas Component
 * Main component for rendering and controlling simulations
 */

import { useEffect, useRef, useState } from "react";
import { SimulationConfig } from "@/types/simulation";
import { SimulationEngine, SimulationState } from "@/simulations/ai-generator/engine";
import { SimulationRenderer } from "@/simulations/ai-generator/renderer";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { AlertCircle, Play, Pause, RotateCcw, Zap } from "lucide-react";
import { cn } from "@/lib/utils";

interface SimulationCanvasProps {
  config: SimulationConfig | null;
  className?: string;
  onError?: (error: string) => void;
}

export function SimulationCanvas({ config, className, onError }: SimulationCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const engineRef = useRef<SimulationEngine | null>(null);
  const rendererRef = useRef<SimulationRenderer | null>(null);

  const [isRunning, setIsRunning] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [gravity, setGravity] = useState(9.8);
  const [timeScale, setTimeScale] = useState(1);
  const [time, setTime] = useState(0);
  const [objectCount, setObjectCount] = useState(0);
  const [error, setError] = useState<string | null>(null);

  // Initialize simulation when config changes
  useEffect(() => {
    if (!config) return;
    if (!canvasRef.current) return;

    try {
      setError(null);

      // Stop previous simulation
      if (engineRef.current) {
        engineRef.current.stop();
      }

      // Create new engine
      const engine = new SimulationEngine(config);
      engineRef.current = engine;

      // Create renderer
      const renderer = new SimulationRenderer(canvasRef.current);
      rendererRef.current = renderer;

      // Set initial values
      setGravity(config.environment.gravity);
      setTimeScale(config.environment.timeScale || 1);
      setObjectCount(config.objects.length);

      // Start simulation
      engine.start((state) => {
        renderer.render(state, config.environment);
        setTime(state.time);
      });

      setIsRunning(true);
      setIsPaused(false);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      setError(message);
      if (onError) onError(message);
    }

    // Cleanup
    return () => {
      if (engineRef.current) {
        engineRef.current.stop();
      }
    };
  }, [config, onError]);

  // Handle window resize
  useEffect(() => {
    const handleResize = () => {
      if (rendererRef.current && canvasRef.current) {
        rendererRef.current.resize();
      }
    };

    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const handlePlayPause = () => {
    if (!engineRef.current) return;

    if (isPaused) {
      engineRef.current.resume();
      setIsPaused(false);
    } else {
      engineRef.current.pause();
      setIsPaused(true);
    }
  };

  const handleReset = () => {
    if (!engineRef.current) return;

    engineRef.current.reset();
    setTime(0);
    setIsPaused(false);

    if (rendererRef.current) {
      rendererRef.current.clearTrails();
    }
  };

  const handleGravityChange = (value: number[]) => {
    const newGravity = value[0];
    setGravity(newGravity);

    if (engineRef.current) {
      engineRef.current.setGravity(newGravity);
    }
  };

  const handleTimeScaleChange = (value: number[]) => {
    const newTimeScale = value[0];
    setTimeScale(newTimeScale);

    if (engineRef.current) {
      engineRef.current.setTimeScale(newTimeScale);
    }
  };

  return (
    <div className={cn("h-full flex flex-col gap-4", className)}>
      {/* Canvas Area */}
      <Card className="flex-1 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 border-purple-500/20 shadow-xl overflow-hidden relative">
        {error && (
          <div className="absolute inset-0 flex items-center justify-center bg-slate-900/80 backdrop-blur-sm z-50">
            <div className="bg-slate-800 border border-red-500/30 rounded-lg p-6 max-w-md">
              <div className="flex items-center gap-3 mb-3">
                <AlertCircle className="w-6 h-6 text-red-400" />
                <h3 className="text-lg font-semibold text-red-300">Error</h3>
              </div>
              <p className="text-sm text-red-300 mb-4">{error}</p>
              <Button
                onClick={() => setError(null)}
                className="bg-red-500/20 hover:bg-red-500/30 text-red-300"
              >
                Dismiss
              </Button>
            </div>
          </div>
        )}

        {!config ? (
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <Zap className="w-12 h-12 text-purple-400 mx-auto mb-4" />
              <p className="text-slate-400">Generate a simulation to begin</p>
            </div>
          </div>
        ) : (
          <canvas ref={canvasRef} className="w-full h-full block" />
        )}
      </Card>

      {/* Controls Panel */}
      {config && (
        <Card className="bg-gradient-to-r from-slate-900 via-slate-800 to-slate-900 border-purple-500/20 p-6">
          {/* Control Buttons */}
          <div className="grid grid-cols-3 gap-3 mb-6">
            <Button
              onClick={handlePlayPause}
              className="bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white"
            >
              {isPaused ? (
                <>
                  <Play className="w-4 h-4 mr-2" />
                  Resume
                </>
              ) : (
                <>
                  <Pause className="w-4 h-4 mr-2" />
                  Pause
                </>
              )}
            </Button>

            <Button
              onClick={handleReset}
              className="bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 text-white"
            >
              <RotateCcw className="w-4 h-4 mr-2" />
              Reset
            </Button>

            <div className="text-right text-sm text-slate-400 flex items-center justify-end">
              <span>{time.toFixed(2)}s</span>
            </div>
          </div>

          {/* Gravity Slider */}
          <div className="mb-5">
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm font-medium text-slate-300">Gravity</label>
              <span className="text-sm text-slate-400 font-mono">{gravity.toFixed(1)} m/s²</span>
            </div>
            <Slider
              value={[gravity]}
              onValueChange={handleGravityChange}
              min={0}
              max={20}
              step={0.1}
              className="w-full"
            />
          </div>

          {/* Time Scale Slider */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm font-medium text-slate-300">Speed</label>
              <span className="text-sm text-slate-400 font-mono">{timeScale.toFixed(2)}x</span>
            </div>
            <Slider
              value={[timeScale]}
              onValueChange={handleTimeScaleChange}
              min={0.1}
              max={2}
              step={0.1}
              className="w-full"
            />
          </div>

          {/* Info */}
          <div className="mt-6 pt-4 border-t border-purple-500/20 text-xs text-slate-400 space-y-1">
            <p>Objects: {objectCount}</p>
            <p>Status: {isPaused ? "⏸ Paused" : "▶ Running"}</p>
          </div>
        </Card>
      )}
    </div>
  );
}
