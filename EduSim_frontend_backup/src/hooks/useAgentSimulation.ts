import { useState, useCallback } from "react";
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
  generate: (prompt: string, complexity?: string, topic?: string) => Promise<void>;
  generateStream: (prompt: string, complexity?: string, topic?: string) => Promise<void>;
  reset: () => void;
  clearError: () => void;
}

// DSL pipeline stage → progress percentage mapping
const DSL_STAGE_PROGRESS: Record<string, number> = {
  "Initializing":               5,
  "Detecting subject":         10,
  "Retrieving textbook":       20,
  "Retrieved":                 30,
  "Extracting formulas":       40,
  "Extracted":                 50,
  "Synthesizing Physics DSL":  60,
  "Sanitizing":                72,
  "Validating DSL":            82,
  "Saving simulation":         92,
};

/**
 * Custom hook for autonomous AI simulation generation.
 *
 * Handles:
 * - Non-streaming and streaming DSL generation
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

  const reset = useCallback(() => {
    setSimulation(null);
    setLoading(false);
    setStreaming(false);
    setError(null);
    setProgress(null);
    setProgressPercentage(0);
  }, []);

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
        setSimulation(result);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Generation failed");
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
            setProgress(progressUpdate);

            if (progressUpdate.progress !== undefined) {
              setProgressPercentage(progressUpdate.progress);
            } else {
              // Infer percentage from DSL stage label
              const matchedPct = Object.entries(DSL_STAGE_PROGRESS).find(([key]) =>
                progressUpdate.stage?.includes(key)
              )?.[1];
              if (matchedPct !== undefined) setProgressPercentage(matchedPct);
            }

            if (progressUpdate.error) {
              setError(`Error: ${progressUpdate.error}`);
              setStreaming(false);
              setLoading(false);
            }
          },
          (result) => {
            setSimulation(result);
            setError(null);
            setStreaming(false);
            setLoading(false);
            setProgressPercentage(100);
          },
          complexity,
          topic
        );
      } catch (err) {
        setError(err instanceof Error ? err.message : "Streaming generation failed");
        setSimulation(null);
        setStreaming(false);
        setLoading(false);
      }
    },
    [reset]
  );

  return {
    simulation,
    loading,
    streaming,
    error,
    progress,
    progressPercentage,
    generate,
    generateStream,
    reset,
    clearError,
  };
}

