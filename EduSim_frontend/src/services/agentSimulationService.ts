/**
 * Autonomous AI Simulation Generation Agent Service
 * 
 * Handles communication with the backend agent endpoints for:
 * - Prompt analysis and topic detection
 * - Context retrieval from RAG system
 * - AI-powered HTML generation
 * - Streaming generation with progress updates
 */

export interface SimulationTopicInfo {
  topic: string;
  subject: "physics" | "chemistry" | "astronomy" | "biology" | "mathematics";
  subtopic?: string;
  complexity: "beginner" | "medium" | "advanced";
  grade_level?: string;
}

export interface SimulationInteractionInfo {
  name: string;
  label: string;
  type: "slider" | "button" | "input" | "toggle";
  min?: number;
  max?: number;
  default?: number;
  unit?: string;
}

export interface SimulationContextInfo {
  topic: string;
  formulas: string[];
  constants: string[];
  laws: string[];
  definitions: string[];
  worked_examples: string[];
  sources: Array<{
    source: string;
    page: string | number;
    text_snippet?: string;
  }>;
}

export interface AgentGeneratedSimulation {
  id: string;
  title: string;
  description: string;
  topic: SimulationTopicInfo;
  html: string;
  formula?: string;
  formulas: string[];
  learning_objectives: string[];
  related_concepts: string[];
  interactions: SimulationInteractionInfo[];
  context: SimulationContextInfo;
  html_path?: string;
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

class AgentSimulationService {
  private apiBaseUrl: string;

  constructor() {
    this.apiBaseUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
  }

  /**
   * Generate a simulation using the autonomous agent (non-streaming).
   * 
   * Args:
   *   prompt: Natural language prompt (e.g., "Create a projectile motion simulation")
   *   complexity: Optional complexity override (beginner, medium, advanced)
   *   topic: Optional topic override
   * 
   * Returns:
   *   AgentGeneratedSimulation with complete metadata and HTML
   */
  async generate(
    prompt: string,
    complexity?: string,
    topic?: string
  ): Promise<AgentGeneratedSimulation> {
    const response = await fetch(`${this.apiBaseUrl}/api/simulations/agent/generate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
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
   * - started: Initial event with simulation ID
   * - progress: Stage updates (10%, 25%, 35%, 50%, 70%, 80%, 90%, 95%)
   * - complete: Final event with complete simulation
   * - error: Error event if generation fails
   * 
   * Args:
   *   prompt: Natural language prompt
   *   onProgress: Callback for progress updates
   *   onComplete: Callback when generation completes
   *   complexity: Optional complexity override
   *   topic: Optional topic override
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
        headers: {
          "Content-Type": "application/json",
        },
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
                  // Streaming complete
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

  /**
   * Analyze a prompt to detect topic and subject.
   * 
   * This is a client-side helper that mimics the backend analysis.
   */
  analyzePrompt(prompt: string): SimulationTopicInfo {
    const promptLower = prompt.toLowerCase();
    
    // Simple topic detection
    const subjects = {
      physics: ["motion", "force", "velocity", "gravity", "wave", "light", "projectile", "pendulum"],
      chemistry: ["molecule", "atom", "bond", "reaction", "element"],
      astronomy: ["planet", "star", "galaxy", "orbit", "space"],
      biology: ["cell", "dna", "organism", "photosynthesis"],
      mathematics: ["function", "graph", "equation", "algebra"],
    };

    let subject: SimulationTopicInfo["subject"] = "physics";
    for (const [subj, keywords] of Object.entries(subjects)) {
      if (keywords.some(kw => promptLower.includes(kw))) {
        subject = subj as SimulationTopicInfo["subject"];
        break;
      }
    }

    const complexityKeywords = {
      beginner: ["simple", "basic", "easy"],
      medium: ["explain", "show", "visualize"],
      advanced: ["complex", "detailed", "mathematical"],
    };

    let complexity: SimulationTopicInfo["complexity"] = "medium";
    for (const [level, keywords] of Object.entries(complexityKeywords)) {
      if (keywords.some(kw => promptLower.includes(kw))) {
        complexity = level as SimulationTopicInfo["complexity"];
        break;
      }
    }

    return {
      topic: `${subject.charAt(0).toUpperCase() + subject.slice(1)} Simulation`,
      subject: subject as SimulationTopicInfo["subject"],
      complexity,
    };
  }

  /**
   * Get safe HTML for rendering in iframe.
   * Performs additional validation on client side.
   */
  isSafeHtml(html: string): boolean {
    const blockedPatterns = [
      /<script[^>]+src\s*=/i,
      /https?:\/\//i,
      /\bfetch\s*\(/i,
      /XMLHttpRequest/i,
      /WebSocket/i,
      /window\.open/i,
      /\btop\./i,
      /\bparent\./i,
      /\beval\s*\(/i,
      /new\s+Function\s*\(/i,
    ];

    return !blockedPatterns.some(pattern => pattern.test(html));
  }

  async reportRuntimeError(simulationId: string | null, payload: any): Promise<void> {
    try {
      await fetch(`${this.apiBaseUrl}/api/simulations/agent/error-report${simulationId ? `?simulation_id=${encodeURIComponent(simulationId)}` : ""}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
    } catch (e) {
      console.error("Failed to report runtime error", e);
    }
  }

  async reportRuntimeIntelligence(report: any): Promise<void> {
    try {
      await fetch(`${this.apiBaseUrl}/api/simulations/runtime/report`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(report),
      });
    } catch (e) {
      console.error("Failed to report runtime intelligence", e);
    }
  }
}

export const agentSimulationService = new AgentSimulationService();

