export type LawKey = "first-law" | "second-law" | "third-law";

export type LearningMode = "visual" | "interactive" | "real-life" | "formula" | "gamified";

export type LawQuizQuestionType = "mcq" | "prediction" | "drag-drop";

export type LawChallengeKey = "first-law" | "second-law" | "third-law";

export type LawWhatIfTopic =
  | "gravity-zero"
  | "mass-doubles"
  | "friction-disappears"
  | "force-doubles";

export interface LawTutorInsight {
  summary: string;
  whyThisHappened: string;
  adaptiveExplanation: string;
  followUpQuestions: string[];
  recommendations: string[];
  mistakeDetection: string[];
}

export interface LawChallenge {
  law: LawChallengeKey;
  title: string;
  objective: string;
  timerSeconds: number;
  target: Record<string, number | string>;
  scoringGuide: string[];
  badges: string[];
  hints: string[];
}

export interface LawQuizQuestion {
  id: string;
  type: LawQuizQuestionType;
  prompt: string;
  options?: string[];
  correctAnswer: string;
  explanation: string;
  hint: string;
  concept: string;
  dragItems?: string[];
  dropTargets?: string[];
}

export interface LawAnalyticsSnapshot {
  timeSpentSeconds: number;
  interactions: number;
  experimentsCompleted: number;
  quizAccuracy: number;
  strengths: string[];
  weaknesses: string[];
  recommendedMode: LearningMode;
  progressPercent: number;
}

export interface LawWhatIfResponse {
  prompt: string;
  law: LawKey;
  explanation: string;
  predictedOutcome: string;
  followUp: string[];
  recommendedMode: LearningMode;
}

export interface LawExperimentRecord {
  id: string;
  label: string;
  law: LawKey;
  learningMode: LearningMode;
  savedAt: number;
  config: LawSimulationConfig;
}

export type LawEngineName = "inertia_engine" | "force_engine" | "reaction_engine";

export type LawScene = string;

export interface LawCurriculumPath {
  class: "9";
  subject: "physics";
  chapter: "laws-of-motion";
  topic: LawKey;
}

export interface LawMetric {
  label: string;
  value: string;
  unit: string;
  color: string;
}

export interface LawSimulationObject {
  id: string;
  shape: "circle" | "rect" | "rocket" | "skater" | "arrow" | "text" | "particle";
  x: number;
  y: number;
  vx?: number;
  vy?: number;
  radius?: number;
  width?: number;
  height?: number;
  mass?: number;
  color?: string;
  label?: string;
  secondaryLabel?: string;
  trail?: boolean;
  opacity?: number;
}

export interface LawControlState {
  gravity: number;
  friction: number;
  mass: number;
  force: number;
  speed: number;
  slowMotion: boolean;
  showVectors: boolean;
  showGraphs: boolean;
}

export interface LawSimulationConfig {
  law: LawKey;
  engine: LawEngineName;
  title: string;
  subtitle: string;
  scene: LawScene;
  learningMode: LearningMode;
  formula: string;
  formulaBreakdown: string[];
  explanation: string;
  curriculum: LawCurriculumPath;
  environment: {
    gravity: number;
    friction: number;
    timeScale: number;
    background: "lab" | "space" | "ice" | "road" | "construction" | "underwater" | "mountain";
  };
  controls: LawControlState;
  objects: LawSimulationObject[];
  interactions: string[];
  tutorHints: string[];
  examples: string[];
  metrics: LawMetric[];
  quiz: {
    prompt: string;
    answer: string;
  };
  narration: string;
  challenge?: LawChallenge;
  quizBank?: LawQuizQuestion[];
  accessibilityNotes?: string[];
  recommendedPath?: string[];
}

export interface LawGenerationResponse {
  success: boolean;
  simulation?: LawSimulationConfig;
  reasoning?: string;
  tutor?: string;
  challenge?: LawChallenge;
  quiz?: LawQuizQuestion[];
  analytics?: LawAnalyticsSnapshot;
  whatIf?: LawWhatIfResponse;
  adaptive?: LawTutorInsight;
  retrieval?: {
    law: LawKey;
    summary: string;
    formulas: string[];
    examples: string[];
    snippets: string[];
  };
  error?: string;
}

export interface LawTutorResponse {
  success: boolean;
  answer?: string;
  references?: string[];
  insights?: LawTutorInsight;
  error?: string;
}

export const LAW_ROUTE_BY_KEY: Record<LawKey, string> = {
  "first-law": "/simulation/class9/physics/laws-of-motion/first-law",
  "second-law": "/simulation/class9/physics/laws-of-motion/second-law",
  "third-law": "/simulation/class9/physics/laws-of-motion/third-law",
};
