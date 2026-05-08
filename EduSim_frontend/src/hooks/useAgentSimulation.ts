import { useState, useCallback, useEffect } from "react";
import {
  agentSimulationService,
  AgentGeneratedSimulation,
  AgentStreamProgress,
} from "@/services/agentSimulationService";

export interface UseAgentSimulationState {
  simulation: AgentGeneratedSimulation | null;
  loading: boolean;
  streaming: boolean;
  error: string | null;
  progress: AgentStreamProgress | null;
  progressPercentage: number;
}

export interface UseAgentSimulationActions {
  generate: (
    prompt: string,
    complexity?: string,
    topic?: string
  ) => Promise<void>;
  generateStream: (
    prompt: string,
    complexity?: string,
    topic?: string
  ) => Promise<void>;
  reset: () => void;
  clearError: () => void;
}

/**
 * Custom hook for autonomous AI simulation generation.
 * 
 * Handles:
 * - Non-streaming and streaming generation
 * - Progress tracking
 * - Error handling
 * - State management
 */
export function useAgentSimulation(): UseAgentSimulationState & UseAgentSimulationActions {
  const [simulation, setSimulation] = useState<AgentGeneratedSimulation | null>(null);
  const [loading, setLoading] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState<AgentStreamProgress | null>(null);
  const [progressPercentage, setProgressPercentage] = useState(0);

  // Runtime Intelligence Bridge
  useEffect(() => {
    const handleMessage = async (event: MessageEvent) => {
      const { type, payload, simId } = event.data;
      if (!type || !simId) return;

      if (type.startsWith("sim_")) {
        console.log(`[Runtime Intelligence] ${type}:`, payload);
        
        // Report to backend
        const report = {
          simulation_id: simId,
          fps_avg: payload.fps || 60,
          js_errors: type === "sim_error" ? [payload] : [],
          interaction_count: type === "sim_interaction" ? 1 : 0,
          physics_stability: payload.stability || 1.0,
        };

        try {
          const response = await agentSimulationService.reportRuntimeIntelligence(report) as any;
          if (response?.repair_triggered) {
            console.warn("Autonomous repair triggered for simulation:", simId);
            // In a full implementation, we might show a "Repairing..." toast here
          }
        } catch (err) {
          console.error("Failed to process runtime intelligence report", err);
        }
      }
    };

    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, []);

  const reset = useCallback(() => {
    setSimulation(null);
    setLoading(false);
    setStreaming(false);
    setError(null);
    setProgress(null);
    setProgressPercentage(0);
  }, []);

  // ... rest of the hook implementation ...


  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const generate = useCallback(
    async (prompt: string, complexity?: string, topic?: string) => {
      if (!prompt.trim()) {
        setError("Please enter a prompt");
        return;
      }

      reset();
      setLoading(true);

      try {
        const result = await agentSimulationService.generate(prompt, complexity, topic);
        
        // Validate HTML safety
        if (!agentSimulationService.isSafeHtml(result.html)) {
          throw new Error("Generated HTML failed safety validation");
        }

        setSimulation(result);
        setError(null);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Generation failed";
        setError(errorMessage);
        setSimulation(null);
      } finally {
        setLoading(false);
      }
    },
    [reset]
  );

  const generateStream = useCallback(
    async (prompt: string, complexity?: string, topic?: string) => {
      if (!prompt.trim()) {
        setError("Please enter a prompt");
        return;
      }

      reset();
      setLoading(true);
      setStreaming(true);

      try {
        await agentSimulationService.generateStream(
          prompt,
          (progressUpdate) => {
            // Update progress state
            setProgress(progressUpdate);

            // Update progress percentage based on stage
            if (progressUpdate.progress !== undefined) {
              setProgressPercentage(progressUpdate.progress);
            } else {
              // Infer progress from stage
              const stageProgressMap: Record<string, number> = {
                "Analyzing prompt": 10,
                "Detected": 15,
                "Retrieving textbook context": 25,
                "Retrieved context": 35,
                "Building enhanced prompt": 40,
                "Generating simulation": 50,
                "HTML generated": 70,
                "Saving generated simulation": 80,
                "Building response metadata": 90,
                "Storing metadata": 95,
              };

              const percentage = Object.entries(stageProgressMap).find(
                ([key]) => progressUpdate.stage?.includes(key)
              )?.[1] || progressPercentage;

              setProgressPercentage(percentage);
            }

            // Handle errors
            if (progressUpdate.error) {
              setError(`Error: ${progressUpdate.error}`);
              setStreaming(false);
              setLoading(false);
            }
          },
          (result) => {
            // Validate HTML safety
            if (!agentSimulationService.isSafeHtml(result.html)) {
              setError("Generated HTML failed safety validation");
              setSimulation(null);
            } else {
              setSimulation(result);
              setError(null);
            }
            
            setStreaming(false);
            setLoading(false);
            setProgressPercentage(100);
          },
          complexity,
          topic
        );
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : "Streaming generation failed";
        setError(errorMessage);
        setSimulation(null);
        setStreaming(false);
        setLoading(false);
      }
    },
    [reset, progressPercentage]
  );

  return {
    // State
    simulation,
    loading,
    streaming,
    error,
    progress,
    progressPercentage,
    // Actions
    generate,
    generateStream,
    reset,
    clearError,
  };
}
