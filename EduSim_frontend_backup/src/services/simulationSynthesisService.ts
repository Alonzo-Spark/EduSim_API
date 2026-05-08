export interface SimulationSourceRef {
  source: string;
  page: number | string;
}

export interface SynthesizedSimulation {
  id: string;
  title: string;
  description: string;
  formula: string;
  sources: SimulationSourceRef[];
  topic: string;
  prompt: string;
  timestamp: string;
  html?: string;
  subject?: string;
}

interface GenerateResponse extends SynthesizedSimulation {
  success: boolean;
}

interface ListResponse {
  success: boolean;
  items: SynthesizedSimulation[];
}

interface GetResponse extends SynthesizedSimulation {
  success: boolean;
}

export interface StreamProgress {
  stage: string;
  id?: string;
  error?: string;
  type?: string;
}

type StreamCallback = (progress: StreamProgress) => void;
type StreamCompleteCallback = (simulation: SynthesizedSimulation) => void;

class SimulationSynthesisService {
  private apiBaseUrl: string;

  constructor() {
    this.apiBaseUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
  }

  async generate(prompt: string, topic?: string): Promise<SynthesizedSimulation> {
    const response = await fetch(`${this.apiBaseUrl}/api/simulations/synthesis/generate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ prompt, topic }),
    });

    const data = (await response.json()) as GenerateResponse | { detail?: string };
    if (!response.ok) {
      throw new Error((data as { detail?: string }).detail || "Simulation generation failed");
    }

    return data as SynthesizedSimulation;
  }

  async list(limit = 30): Promise<SynthesizedSimulation[]> {
    const response = await fetch(`${this.apiBaseUrl}/api/simulations/synthesis/list?limit=${limit}`);
    const data = (await response.json()) as ListResponse | { detail?: string };

    if (!response.ok) {
      throw new Error((data as { detail?: string }).detail || "Failed to load simulations");
    }

    return (data as ListResponse).items;
  }

  async getById(id: string): Promise<SynthesizedSimulation> {
    const response = await fetch(`${this.apiBaseUrl}/api/simulations/synthesis/${id}`);
    const data = (await response.json()) as GetResponse | { detail?: string };

    if (!response.ok) {
      throw new Error((data as { detail?: string }).detail || "Failed to load simulation");
    }

    return data as SynthesizedSimulation;
  }

  getExportUrl(id: string): string {
    return `${this.apiBaseUrl}/api/simulations/synthesis/${id}/export`;
  }

  async generateStream(
    prompt: string,
    onProgress: StreamCallback,
    onComplete: StreamCompleteCallback,
    topic?: string
  ): Promise<void> {
    const response = await fetch(
      `${this.apiBaseUrl}/api/simulations/synthesis/generate-stream`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ prompt, topic }),
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
                  onProgress(data as StreamProgress);
                } else if (eventType === "complete") {
                  onComplete(data as SynthesizedSimulation);
                } else if (eventType === "error") {
                  onProgress(data as StreamProgress);
                }
              } catch (e) {
                console.error("Failed to parse SSE data:", dataStr);
              }
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }
}

export const simulationSynthesisService = new SimulationSynthesisService();