export interface SimulationResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  detail?: string;
}

export interface MomentumTrajectoryPoint {
  t: number;
  v: number;
  a: number;
  f: number;
  x: number;
}

export interface MomentumData {
  acceleration: number;
  force: number;
  mass: number;
  trajectory: MomentumTrajectoryPoint[];
}

export interface ActionReactionTrajectoryPoint {
  t: number;
  position: number;
}

export interface ActionReactionData {
  acceleration1: number;
  acceleration2: number;
  trajectories: {
    object1: ActionReactionTrajectoryPoint[];
    object2: ActionReactionTrajectoryPoint[];
  };
}

export interface RagResponseData {
  answer: string;
}

class PhysicsSimulationApi {
  private apiBaseUrl: string;

  constructor() {
    this.apiBaseUrl = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";
  }

  async simulateMomentum(mass: number, force: number): Promise<SimulationResponse<MomentumData>> {
    try {
      const response = await fetch(`${this.apiBaseUrl}/api/simulations/momentum`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ mass, force }),
      });

      const data = await response.json();
      
      if (!response.ok) {
        return { success: false, error: data.detail || "API Error" };
      }

      return data;
    } catch (error) {
      return { success: false, error: "Network Error" };
    }
  }

  async simulateActionReaction(mass1: number, mass2: number, force: number): Promise<SimulationResponse<ActionReactionData>> {
    try {
      const response = await fetch(`${this.apiBaseUrl}/api/simulations/action-reaction`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ mass1, mass2, force }),
      });

      const data = await response.json();

      if (!response.ok) {
        return { success: false, error: data.detail || "API Error" };
      }

      return data;
    } catch (error) {
      return { success: false, error: "Network Error" };
    }
  }

  async queryRag(query: string): Promise<SimulationResponse<RagResponseData>> {
    try {
      const response = await fetch(`${this.apiBaseUrl}/api/rag/query`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query }),
      });

      const data = await response.json();

      if (!response.ok) {
        return { success: false, error: data.detail || "RAG API Error" };
      }

      // Map { success: true, answer: "..." } to SimulationResponse format
      return {
        success: true,
        data: { answer: data.answer }
      };
    } catch (error) {
      return { success: false, error: "Network Error" };
    }
  }
}

export const physicsSimulationApi = new PhysicsSimulationApi();
