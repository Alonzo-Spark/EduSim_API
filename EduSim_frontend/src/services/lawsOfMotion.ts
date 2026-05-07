import type {
  LawAnalyticsSnapshot,
  LawChallenge,
  LawGenerationResponse,
  LawKey,
  LawQuizQuestion,
  LawSimulationConfig,
  LawTutorResponse,
  LearningMode,
  LawWhatIfResponse,
} from "@/types/lawsOfMotion";

class LawsOfMotionService {
  private apiBaseUrl: string;

  constructor() {
    this.apiBaseUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
  }

  async generateSimulation(
    prompt: string,
    law: LawKey,
    learningMode: LearningMode,
    context?: string,
  ): Promise<LawGenerationResponse> {
    const response = await fetch(`${this.apiBaseUrl}/api/laws-of-motion/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt, law_key: law, learning_mode: learningMode, context }),
    });

    const data = (await response.json()) as LawGenerationResponse;

    if (!response.ok) {
      return { success: false, error: data.error || `API error: ${response.status}` };
    }

    return data;
  }

  async askTutor(
    question: string,
    law: LawKey,
    learningMode: LearningMode,
    context?: string,
  ): Promise<LawTutorResponse> {
    const response = await fetch(`${this.apiBaseUrl}/api/laws-of-motion/tutor`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, law_key: law, learning_mode: learningMode, context }),
    });

    return (await response.json()) as LawTutorResponse;
  }

  async generateChallenge(
    law: LawKey,
    learningMode: LearningMode,
    context?: string,
  ): Promise<{ success: boolean; challenge?: LawChallenge; error?: string }> {
    const response = await fetch(`${this.apiBaseUrl}/api/laws-of-motion/challenge`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ law_key: law, learning_mode: learningMode, context }),
    });

    return response.json();
  }

  async generateQuiz(
    law: LawKey,
    learningMode: LearningMode,
    context?: string,
  ): Promise<{ success: boolean; quiz?: LawQuizQuestion[]; error?: string }> {
    const response = await fetch(`${this.apiBaseUrl}/api/laws-of-motion/quiz`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ law_key: law, learning_mode: learningMode, context }),
    });

    return response.json();
  }

  async analyzeLearning(
    law: LawKey,
    payload: Record<string, unknown>,
  ): Promise<{ success: boolean; analytics?: LawAnalyticsSnapshot; error?: string }> {
    const response = await fetch(`${this.apiBaseUrl}/api/laws-of-motion/analytics`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ law_key: law, profile: payload }),
    });

    return response.json();
  }

  async explainWhatIf(
    law: LawKey,
    prompt: string,
    learningMode: LearningMode,
    context?: string,
  ): Promise<{ success: boolean; whatIf?: LawWhatIfResponse; error?: string }> {
    const response = await fetch(`${this.apiBaseUrl}/api/laws-of-motion/what-if`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ law_key: law, prompt, learning_mode: learningMode, context }),
    });

    return response.json();
  }

  async getCatalog(): Promise<{
    success: boolean;
    laws: Array<Pick<LawSimulationConfig, "law" | "title" | "subtitle" | "formula">>;
  }> {
    const response = await fetch(`${this.apiBaseUrl}/api/laws-of-motion/catalog`);
    return response.json();
  }
}

export const lawsOfMotionService = new LawsOfMotionService();
