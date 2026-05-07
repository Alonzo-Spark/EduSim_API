/**
 * Hook for managing simulation generation state
 */

import { useState, useCallback, useRef } from "react";
import { SimulationConfig } from "@/types/simulation";
import { simulationGenerator } from "@/services/simulationGenerator";

export interface SimulationState {
  config: SimulationConfig | null;
  loading: boolean;
  error: string | null;
  reasoning?: string;
}

export function useSimulationGenerator() {
  const [state, setState] = useState<SimulationState>({
    config: null,
    loading: false,
    error: null,
  });

  const abortControllerRef = useRef<AbortController | null>(null);

  const generate = useCallback(async (prompt: string, educationalContext?: string) => {
    // Cancel previous request if still pending
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    setState({
      config: null,
      loading: true,
      error: null,
    });

    const result = await simulationGenerator.generateSimulation(prompt, educationalContext);

    if (!abortControllerRef.current.signal.aborted) {
      setState({
        config: result.simulation || null,
        loading: false,
        error: result.error || null,
        reasoning: result.reasoning,
      });
    }

    return result;
  }, []);

  const clear = useCallback(() => {
    setState({
      config: null,
      loading: false,
      error: null,
    });
  }, []);

  const setError = useCallback((error: string) => {
    setState((prev) => ({
      ...prev,
      error,
    }));
  }, []);

  return {
    ...state,
    generate,
    clear,
    setError,
  };
}
