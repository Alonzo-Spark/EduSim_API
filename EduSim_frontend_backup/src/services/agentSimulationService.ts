/**
 * Autonomous AI Simulation Generation Agent Service
 *
 * Handles communication with the backend agent endpoints for:
 * - Prompt analysis and topic detection
 * - Context retrieval from RAG system
 * - AI-powered Physics DSL generation
 * - Streaming generation with progress updates
 */

// =========================================================
// Physics DSL Types
// =========================================================

export interface DSLEnvironment {
  gravity: number;
  friction: number;
  air_resistance: number;
}

export interface DSLEntity {
  id: string;
  type: string;
  mass: number | null;
  properties: Record<string, unknown>;
}

export interface DSLInteraction {
  type: string;
  target: string;
  parameters: Record<string, unknown>;
}

export interface DSLVisualization {
  type: string;
}

export interface PhysicsDSL {
  simulation_type: string;
  topic: string;
  environment: DSLEnvironment;
  entities: DSLEntity[];
  interactions: DSLInteraction[];
  visualizations: DSLVisualization[];
  equations: string[];
}

// =========================================================
// Simulation Response Types
// =========================================================

export interface SimulationTopicInfo {
  topic: string;
  subject: "physics" | "chemistry" | "astronomy" | "biology" | "mathematics";
  subtopic?: string;
  complexity: "beginner" | "medium" | "advanced";
}

export interface SimulationContextInfo {
  topic: string;
  formulas: string[];
  constants: string[];
  laws: string[];
  definitions: string[];
  sources: Array<{
    source: string;
    page: string | number;
  }>;
}

export interface AgentGeneratedSimulation {
  id: string;
  title: string;
  description: string;
  topic: SimulationTopicInfo;
  /** Physics DSL JSON — the core output of the compiler pipeline */
  dsl: PhysicsDSL;
  formula?: string;
  formulas: string[];
  learning_objectives: string[];
  related_concepts: string[];
  context: SimulationContextInfo;
  timestamp: string;
  generation_stages: string[];
}

export interface AgentGenerateRequest {
  prompt: string;
  topic?: string;
  complexity?: "beginner" | "medium" | "advanced";
  include_answers?: boolean;
  streaming?: boolean;
}

export interface AgentStreamProgress {
  stage: string;
  progress?: number;
  message?: string;
  id?: string;
  error?: string;
  type?: string;
}

type AgentProgressCallback = (progress: AgentStreamProgress) => void;
type AgentCompleteCallback = (simulation: AgentGeneratedSimulation) => void;

// =========================================================
// Service Class
// =========================================================

class AgentSimulationService {
  private apiBaseUrl: string;

  constructor() {
    this.apiBaseUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
  }

  /**
   * Generate a simulation using the autonomous agent (non-streaming).
   * Returns a Physics DSL JSON object — not HTML.
   */
  async generate(
    prompt: string,
    complexity?: string,
    topic?: string
  ): Promise<AgentGeneratedSimulation> {
    const response = await fetch(`${this.apiBaseUrl}/api/simulations/agent/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        prompt,
        topic,
        complexity,
        include_answers: true,
        streaming: false,
      } as AgentGenerateRequest),
    });

    const data = (await response.json()) as AgentGeneratedSimulation | { detail?: string };
    if (!response.ok) {
      throw new Error((data as { detail?: string }).detail || "Agent generation failed");
    }

    return data as AgentGeneratedSimulation;
  }

  /**
   * Generate a simulation with streaming progress updates.
   *
   * Emits SSE events at each stage:
   * - started:  Initial event with simulation ID
   * - progress: Stage updates
   * - complete: Final event with full simulation (DSL)
   * - error:    Error event if generation fails
   */
  async generateStream(
    prompt: string,
    onProgress: AgentProgressCallback,
    onComplete: AgentCompleteCallback,
    complexity?: string,
    topic?: string
  ): Promise<void> {
    const response = await fetch(
      `${this.apiBaseUrl}/api/simulations/agent/generate-stream`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt,
          topic,
          complexity,
          include_answers: true,
          streaming: true,
        } as AgentGenerateRequest),
      }
    );

    if (!response.ok || !response.body) {
      throw new Error("Failed to start streaming generation");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines[lines.length - 1];

        for (let i = 0; i < lines.length - 1; i++) {
          const line = lines[i].trim();
          if (!line) continue;

          if (line.startsWith("event:")) {
            const eventType = line.replace("event:", "").trim();
            const dataLine = lines[++i];

            if (dataLine?.startsWith("data:")) {
              const dataStr = dataLine.replace("data:", "").trim();
              try {
                const data = JSON.parse(dataStr);

                if (eventType === "progress" || eventType === "started") {
                  onProgress(data as AgentStreamProgress);
                } else if (eventType === "complete") {
                  onComplete(data as AgentGeneratedSimulation);
                } else if (eventType === "error") {
                  onProgress(data as AgentStreamProgress);
                } else if (eventType === "done") {
                  break;
                }
              } catch (e) {
                console.error("Failed to parse SSE data:", dataStr, e);
              }
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }

  /** Client-side subject detection for UI labelling */
  analyzePrompt(prompt: string): SimulationTopicInfo {
    const promptLower = prompt.toLowerCase();

    const subjects: Record<string, string[]> = {
      physics: ["motion", "force", "velocity", "gravity", "wave", "light", "projectile", "pendulum"],
      chemistry: ["molecule", "atom", "bond", "reaction", "element"],
      astronomy: ["planet", "star", "galaxy", "orbit", "space"],
      biology: ["cell", "dna", "organism", "photosynthesis"],
      mathematics: ["function", "graph", "equation", "algebra"],
    };

    let subject: SimulationTopicInfo["subject"] = "physics";
    for (const [subj, keywords] of Object.entries(subjects)) {
      if (keywords.some((kw) => promptLower.includes(kw))) {
        subject = subj as SimulationTopicInfo["subject"];
        break;
      }
    }

    return {
      topic: `${subject.charAt(0).toUpperCase() + subject.slice(1)} Simulation`,
      subject,
      complexity: "medium",
    };
  }

  async reportRuntimeError(simulationId: string | null, payload: unknown): Promise<void> {
    try {
      await fetch(
        `${this.apiBaseUrl}/api/simulations/agent/error-report${simulationId ? `?simulation_id=${encodeURIComponent(simulationId)}` : ""}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        }
      );
    } catch (e) {
      console.error("Failed to report runtime error", e);
    }
  }
}

export const agentSimulationService = new AgentSimulationService();
