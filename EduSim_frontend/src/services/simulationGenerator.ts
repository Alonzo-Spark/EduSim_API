/**
 * LLM Simulation Generation Service
 * Handles communication with backend AI service
 */

import { SimulationConfig, validateSimulationConfig } from "@/types/simulation";

export interface GenerateSimulationRequest {
  prompt: string;
  educational_context?: string;
}

export interface GenerateSimulationResponse {
  success: boolean;
  simulation?: SimulationConfig;
  error?: string;
  reasoning?: string;
}

class SimulationGeneratorService {
  private apiBaseUrl: string;

  constructor() {
    // Get API base URL from environment or use default
    this.apiBaseUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
  }

  /**
   * Generate simulation from natural language prompt
   */
  async generateSimulation(
    prompt: string,
    educationalContext?: string,
  ): Promise<GenerateSimulationResponse> {
    try {
      const request: GenerateSimulationRequest = {
        prompt,
        educational_context: educationalContext,
      };

      const response = await fetch(`${this.apiBaseUrl}/api/generate-simulation`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const error = await response.json();
        return {
          success: false,
          error: error.detail || `API error: ${response.status}`,
        };
      }

      const data = await response.json();

      // Validate the returned simulation config
      if (!validateSimulationConfig(data.simulation)) {
        return {
          success: false,
          error: "Invalid simulation configuration returned from API",
          reasoning: data.reasoning,
        };
      }

      return {
        success: true,
        simulation: data.simulation,
        reasoning: data.reasoning,
      };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Unknown error";
      return {
        success: false,
        error: `Failed to generate simulation: ${errorMessage}`,
      };
    }
  }

  /**
   * Validate simulation config on the backend
   */
  async validateSimulation(
    config: SimulationConfig,
  ): Promise<{ valid: boolean; errors?: string[] }> {
    try {
      const response = await fetch(`${this.apiBaseUrl}/api/validate-simulation`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(config),
      });

      if (!response.ok) {
        return { valid: false, errors: ["Validation request failed"] };
      }

      return response.json();
    } catch (error) {
      return { valid: false, errors: ["Validation service unavailable"] };
    }
  }

  /**
   * Get example prompts and simulations
   */
  async getExamples(): Promise<
    {
      prompt: string;
      description: string;
    }[]
  > {
    return [
      {
        prompt: "Create a solar system with a sun and 3 planets orbiting",
        description: "Orbital mechanics simulation",
      },
      {
        prompt: "Show 3 red balls bouncing with low gravity",
        description: "Bouncing balls in low gravity",
      },
      {
        prompt: "Create a pendulum on the moon",
        description: "Pendulum motion with lunar gravity",
      },
      {
        prompt: "Simulate projectile motion with initial velocity 20m/s at 45 degrees",
        description: "Classic projectile motion",
      },
      {
        prompt: "Show a spring-mass system oscillating",
        description: "Spring oscillation",
      },
      {
        prompt: "Create a wave in water",
        description: "Wave simulation",
      },
    ];
  }
}

// Export singleton instance
export const simulationGenerator = new SimulationGeneratorService();

export default simulationGenerator;
