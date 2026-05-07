import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { motion } from "framer-motion";
import {
  Activity,
  BadgeCheck,
  CircleAlert,
  Clock3,
  Download,
  Flame,
  GripVertical,
  History,
  Lightbulb,
  Pause,
  Play,
  RefreshCw,
  RotateCcw,
  Save,
  ShieldCheck,
  Sparkles,
  Star,
  TimerReset,
  Trophy,
  Wand2,
} from "lucide-react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import { lawsOfMotionService } from "@/services/lawsOfMotion";
import { useLawLabAnalytics } from "@/hooks/useLawLabAnalytics";
import {
  LEARNING_MODES,
  TutorCard,
  LearningModePicker,
} from "@/components/laws-of-motion/LawPanels";
import type {
  LawAnalyticsSnapshot,
  LawChallenge,
  LawExperimentRecord,
  LawKey,
  LawQuizQuestion,
  LawSimulationConfig,
  LawTutorInsight,
  LearningMode,
} from "@/types/lawsOfMotion";

type SnapshotLike = {
  time?: number;
  description?: string;
  equation?: string;
  hint?: string;
  headline?: string;
  scene?: string;
  stats?: Array<{ label: string; value: string; unit: string; color: string }>;
};

type EngineAction = {
  label: string;
  icon: ReactNode;
  onClick: () => void;
};

type LawLabEnhancementsProps = {
  law: LawKey;
  config: LawSimulationConfig;
  snapshot: SnapshotLike;
  learningMode: LearningMode;
  onLearningModeChange: (mode: LearningMode) => void;
  onApplyConfig: (config: LawSimulationConfig) => void;
  onPrimaryAction?: () => void;
  onSecondaryAction?: () => void;
  onGenerate: () => Promise<void> | void;
  loading: boolean;
  prompt: string;
  setPrompt: (value: string) => void;
  history: string[];
  setHistory: React.Dispatch<React.SetStateAction<string[]>>;
  tutorQuestion: string;
  setTutorQuestion: (value: string) => void;
  tutorAnswer: string;
  tutorLoading: boolean;
  onAskTutor: () => Promise<void> | void;
  tutorInsights?: LawTutorInsight;
  engineActions: EngineAction[];
  title: string;
  recommendedPath?: string[];
};

type StoredExperiment = LawExperimentRecord;

type QuizAnswerState = {
  answer: string;
  correct: boolean | null;
  explanation: string;
};

const MODE_COPY: Record<
  LearningMode,
  { focus: string; overlay: string; tutorial: string; hint: string }
> = {
  visual: {
    focus: "Watch the motion trail, glowing arrows, and vectors before changing any values.",
    overlay: "Visual overlay emphasizes field lines, motion blur, and force direction.",
    tutorial: "Start with the scene and then inspect why the motion changed.",
    hint: "Look for what changes first: position, force, or acceleration.",
  },
  interactive: {
    focus:
      "Treat the lab like an experiment bench. Move one control at a time and compare outcomes.",
    overlay: "Interactive overlay surfaces the active control and immediate response.",
    tutorial: "Use sliders, then predict the result before watching the simulation update.",
    hint: "Changing one variable isolates cause and effect.",
  },
  "real-life": {
    focus: "Connect the setup to buses, rockets, skaters, crates, and everyday motion.",
    overlay: "Real-life overlay replaces abstract labels with practical examples.",
    tutorial: "Translate the physics into a scene you already know.",
    hint: "Ask where you have seen the same rule outside the lab.",
  },
  formula: {
    focus: "Break the equation into symbols, units, and relationships.",
    overlay: "Formula overlay highlights each term and how it changes mathematically.",
    tutorial: "Use the equation as a checklist for the current state.",
    hint: "If one variable increases, which quantity must react?",
  },
  gamified: {
    focus: "Earn points by predicting outcomes and hitting challenge targets.",
    overlay: "Gamified overlay emphasizes score, timer, and achievement states.",
    tutorial: "Compete with the target rather than only watching the motion.",
    hint: "Try to beat your previous score using fewer adjustments.",
  },
};

const QUIZ_FALLBACK: Record<LawKey, LawQuizQuestion[]> = {
  "first-law": [
    {
      id: "first-law-mcq",
      type: "mcq",
      prompt: "Why does a passenger lean forward when a bus stops suddenly?",
      options: [
        "The bus pushes them forward",
        "Their body keeps moving because of inertia",
        "Gravity disappears",
        "Friction always increases",
      ],
      correctAnswer: "Their body keeps moving because of inertia",
      explanation:
        "The passenger keeps moving forward while the bus slows, so inertia makes the motion look like a lurch.",
      hint: "Think about the motion of the passenger before the bus brakes.",
      concept: "inertia",
    },
    {
      id: "first-law-prediction",
      type: "prediction",
      prompt: "What happens if friction becomes almost zero on the moving puck?",
      correctAnswer: "It continues moving at nearly the same speed",
      explanation: "With very little opposing force, the puck keeps its velocity for longer.",
      hint: "Balanced forces and friction are both important here.",
      concept: "friction",
    },
    {
      id: "first-law-dnd",
      type: "drag-drop",
      prompt: "Match each example to the idea it best demonstrates.",
      correctAnswer: "Inertia: hockey puck; Balanced forces: stationary book",
      explanation:
        "The drag-and-drop challenge reinforces the difference between continued motion and no net force.",
      hint: "Classify what is moving and what is staying at rest.",
      concept: "balanced-forces",
      dragItems: ["Hockey puck", "Stationary book"],
      dropTargets: ["Inertia", "Balanced forces"],
    },
  ],
  "second-law": [
    {
      id: "second-law-mcq",
      type: "mcq",
      prompt: "If force stays the same and mass doubles, what happens to acceleration?",
      options: ["It doubles", "It halves", "It becomes zero", "It stays the same"],
      correctAnswer: "It halves",
      explanation:
        "From F = ma, acceleration is inversely proportional to mass when force is fixed.",
      hint: "Keep the force fixed and look at the denominator.",
      concept: "force-mass-acceleration",
    },
    {
      id: "second-law-prediction",
      type: "prediction",
      prompt: "What happens to acceleration when force increases while mass stays constant?",
      correctAnswer: "Acceleration increases",
      explanation: "More force gives more acceleration when mass does not change.",
      hint: "A bigger numerator changes the result.",
      concept: "force",
    },
    {
      id: "second-law-dnd",
      type: "drag-drop",
      prompt: "Match the quantity to its role in F = ma.",
      correctAnswer: "Force: cause; Mass: resistance; Acceleration: response",
      explanation: "The drag-and-drop challenge helps separate cause, resistance, and outcome.",
      hint: "Ask which one is changing because of the other two.",
      concept: "formula-breakdown",
      dragItems: ["Force", "Mass", "Acceleration"],
      dropTargets: ["Cause", "Resistance", "Response"],
    },
  ],
  "third-law": [
    {
      id: "third-law-mcq",
      type: "mcq",
      prompt: "Why do skaters move apart when they push off each other?",
      options: [
        "A force acts on only one skater",
        "Equal and opposite forces act on different bodies",
        "Gravity reverses direction",
        "Momentum disappears",
      ],
      correctAnswer: "Equal and opposite forces act on different bodies",
      explanation:
        "Action and reaction are equal in magnitude but act on separate bodies, so both skaters move.",
      hint: "Think about who feels which force.",
      concept: "action-reaction",
    },
    {
      id: "third-law-prediction",
      type: "prediction",
      prompt: "What happens to the rocket when exhaust gases are pushed backward?",
      correctAnswer: "The rocket moves forward",
      explanation: "The backward push on the exhaust creates a forward reaction on the rocket.",
      hint: "Look at the direction of the reaction force.",
      concept: "rocket-thrust",
    },
    {
      id: "third-law-dnd",
      type: "drag-drop",
      prompt: "Match the scene to the best action-reaction pair.",
      correctAnswer: "Rocket: exhaust backward / rocket forward",
      explanation: "The scene matching makes the momentum exchange visible.",
      hint: "Pick the pair that points in opposite directions.",
      concept: "pairs",
      dragItems: ["Rocket", "Balloon", "Skaters"],
      dropTargets: ["Exhaust backward", "Air out backward", "Push apart"],
    },
  ],
};

function formatSeconds(totalSeconds: number) {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

function parseStat(stats: SnapshotLike["stats"], label: string) {
  const item = stats?.find((entry) => entry.label.toLowerCase() === label.toLowerCase());
  if (!item) {
    return null;
  }

  const parsed = Number.parseFloat(item.value);
  return Number.isFinite(parsed) ? parsed : null;
}

function createExperimentRecord(
  law: LawKey,
  config: LawSimulationConfig,
  learningMode: LearningMode,
): StoredExperiment {
  return {
    id: `${law}-${Date.now()}`,
    label: `${config.title} · ${learningMode}`,
    law,
    learningMode,
    savedAt: Date.now(),
    config,
  };
}

function buildWhatIfPrompt(query: string, law: LawKey) {
  const lowered = query.toLowerCase();

  if (lowered.includes("gravity") && lowered.includes("zero")) {
    return {
      explanation:
        "If gravity becomes zero, weight disappears and only existing motion or other forces remain to change the path.",
      predictedOutcome:
        law === "third-law"
          ? "The rocket still responds to thrust, but weight-related effects vanish."
          : "The object no longer settles downward under weight.",
      followUp: [
        "What force now dominates the motion?",
        "Which parts of the scene become easier to control?",
      ],
      recommendedMode: "visual" as LearningMode,
    };
  }

  if (lowered.includes("mass") && lowered.includes("double")) {
    return {
      explanation:
        "Doubling the mass increases inertia and reduces acceleration if the applied force stays the same.",
      predictedOutcome: "The motion changes more slowly and the graph flattens.",
      followUp: [
        "How much must the force change to keep the same acceleration?",
        "Does this happen in all three laws the same way?",
      ],
      recommendedMode: "formula" as LearningMode,
    };
  }

  if (lowered.includes("friction") && (lowered.includes("disappear") || lowered.includes("zero"))) {
    return {
      explanation:
        "Removing friction takes away a major opposing force, so motion persists more easily.",
      predictedOutcome: "The object keeps moving longer and the system looks smoother.",
      followUp: [
        "What happens to the net force?",
        "Which law is easiest to observe without friction?",
      ],
      recommendedMode: "real-life" as LearningMode,
    };
  }

  return {
    explanation:
      "This scenario changes the balance of forces, so the motion and graphs respond immediately.",
    predictedOutcome: "Expect a visible change in the motion trail and live equation output.",
    followUp: ["Which variable changed first?", "What did the tutor say about the new result?"],
    recommendedMode: "interactive" as LearningMode,
  };
}

function challengeTemplate(law: LawKey): LawChallenge {
  if (law === "first-law") {
    return {
      law,
      title: "Stop the moving crate",
      objective:
        "Use the minimum force and the right timing to stop the object with the least unnecessary disturbance.",
      timerSeconds: 45,
      target: { force: 0, friction: 0.05, speed: 1.5 },
      scoringGuide: [
        "Lower applied force improves score.",
        "Keeping friction low helps.",
        "Stopping motion smoothly earns bonus points.",
      ],
      badges: ["Inertia Guardian", "Balanced Force Pro"],
      hints: ["Let the system drift first.", "Use the brake instead of over-correcting."],
    };
  }

  if (law === "second-law") {
    return {
      law,
      title: "Reach the target acceleration",
      objective: "Adjust force and mass until the acceleration lands in the target band.",
      timerSeconds: 60,
      target: { acceleration: 4.5, force: 8, mass: 3 },
      scoringGuide: [
        "Closer acceleration gives more points.",
        "Avoid large overshoot.",
        "Use the formula to reason before moving sliders.",
      ],
      badges: ["Acceleration Alchemist", "Force Tuner"],
      hints: [
        "Increase force to raise acceleration.",
        "Lower mass if you need a sharper response.",
      ],
    };
  }

  return {
    law,
    title: "Launch the rocket with control",
    objective: "Create a stable thrust pattern and keep the action-reaction pair clear.",
    timerSeconds: 60,
    target: { force: 8, mass: 5, momentum: 40 },
    scoringGuide: [
      "Sustained thrust earns points.",
      "Clear action-reaction labeling boosts the score.",
      "Smooth timing creates the best launch.",
    ],
    badges: ["Thrust Commander", "Momentum Pilot"],
    hints: [
      "Watch the exhaust direction carefully.",
      "Use the launch button after setting the scene.",
    ],
  };
}

function fallbackQuiz(law: LawKey): LawQuizQuestion[] {
  return QUIZ_FALLBACK[law];
}

function lawStrengths(law: LawKey): string[] {
  if (law === "first-law") {
    return ["Inertia explanation", "Force balance reasoning", "Motion trail reading"];
  }

  if (law === "second-law") {
    return ["Force-mass tradeoffs", "Graph interpretation", "Equation breakdown"];
  }

  return ["Action-reaction mapping", "Momentum intuition", "Scene interpretation"];
}

function lawWeaknesses(law: LawKey, analytics: LawAnalyticsSnapshot | undefined): string[] {
  if (analytics?.weaknesses?.length) {
    return analytics.weaknesses;
  }

  if (law === "first-law") {
    return ["Overlooking balanced forces"];
  }

  if (law === "second-law") {
    return ["Confusing larger force with larger mass"];
  }

  return ["Mixing up action and reaction bodies"];
}

function scoreChallenge(
  law: LawKey,
  config: LawSimulationConfig,
  snapshot: SnapshotLike,
  challenge: LawChallenge,
  elapsedSeconds: number,
) {
  const force = config.controls.force;
  const mass = config.controls.mass;
  const friction = config.controls.friction;
  const speed = parseStat(snapshot.stats, "Speed") ?? config.controls.speed;
  const acceleration =
    parseStat(snapshot.stats, "Acceleration") ?? Math.max(0, force / Math.max(1, mass));

  if (law === "first-law") {
    const forceScore = Math.max(0, 50 - force * 6);
    const frictionScore = Math.max(0, 30 - friction * 180);
    const speedScore = Math.max(0, 20 - Math.abs(speed - (challenge.target.speed as number)) * 12);
    return Math.max(
      0,
      Math.min(100, Math.round(forceScore + frictionScore + speedScore - elapsedSeconds * 0.2)),
    );
  }

  if (law === "second-law") {
    const targetAcceleration = challenge.target.acceleration as number;
    const delta = Math.abs(acceleration - targetAcceleration);
    const closeness = Math.max(0, 100 - delta * 18);
    return Math.max(0, Math.min(100, Math.round(closeness - elapsedSeconds * 0.15)));
  }

  const forceScore = Math.max(0, 40 - Math.abs(force - (challenge.target.force as number)) * 5);
  const massScore = Math.max(0, 30 - Math.abs(mass - (challenge.target.mass as number)) * 7);
  const momentumScore = Math.max(
    0,
    30 -
      Math.abs(
        (parseStat(snapshot.stats, "Momentum") ?? 0) - (challenge.target.momentum as number),
      ) *
        0.8,
  );
  return Math.max(
    0,
    Math.min(100, Math.round(forceScore + massScore + momentumScore - elapsedSeconds * 0.15)),
  );
}

function modeLabel(mode: LearningMode) {
  return LEARNING_MODES.find((item) => item.key === mode)?.label ?? mode;
}

function lawFriendlyName(law: LawKey) {
  if (law === "first-law") return "First Law";
  if (law === "second-law") return "Second Law";
  return "Third Law";
}

export function LawLabEnhancements({
  law,
  config,
  snapshot,
  learningMode,
  onLearningModeChange,
  onApplyConfig,
  onPrimaryAction,
  onSecondaryAction,
  onGenerate,
  loading,
  prompt,
  setPrompt,
  history,
  setHistory,
  tutorQuestion,
  setTutorQuestion,
  tutorAnswer,
  tutorLoading,
  onAskTutor,
  tutorInsights,
  engineActions,
  title,
  recommendedPath,
}: LawLabEnhancementsProps) {
  const [quiz, setQuiz] = useState<LawQuizQuestion[]>(() => fallbackQuiz(law));
  const [quizIndex, setQuizIndex] = useState(0);
  const [quizAnswer, setQuizAnswer] = useState("");
  const [quizFeedback, setQuizFeedback] = useState<QuizAnswerState | null>(null);
  const [quizHintVisible, setQuizHintVisible] = useState(false);
  const [dragChoice, setDragChoice] = useState<string | null>(null);
  const [dragPairs, setDragPairs] = useState<Record<string, string>>({});
  const [whatIfPrompt, setWhatIfPrompt] = useState("What if gravity becomes zero?");
  const [whatIfResponse, setWhatIfResponse] = useState<LawAnalyticsSnapshot | null>(null as never);
  const [whatIfAnswer, setWhatIfAnswer] = useState<string>("");
  const [whatIfLoading, setWhatIfLoading] = useState(false);
  const [challenge, setChallenge] = useState<LawChallenge>(() => challengeTemplate(law));
  const [challengeStartedAt, setChallengeStartedAt] = useState<number | null>(null);
  const [challengeRemaining, setChallengeRemaining] = useState(challenge.timerSeconds);
  const [challengeScore, setChallengeScore] = useState<number | null>(null);
  const [challengeActive, setChallengeActive] = useState(false);
  const [savedExperiments, setSavedExperiments] = useState<StoredExperiment[]>(() => {
    if (typeof window === "undefined") {
      return [];
    }

    try {
      const raw = window.localStorage.getItem(`laws-of-motion-experiments:${law}`);
      return raw ? (JSON.parse(raw) as StoredExperiment[]) : [];
    } catch {
      return [];
    }
  });
  const [selectedExperimentId, setSelectedExperimentId] = useState<string | null>(null);
  const [reducedMotion, setReducedMotion] = useState(false);
  const [colorSafePalette, setColorSafePalette] = useState(true);
  const [uiScale, setUiScale] = useState(1);
  const [timeline, setTimeline] = useState<
    Array<{
      t: number;
      force: number;
      mass: number;
      acceleration: number;
      velocity: number;
      momentum: number;
      friction: number;
    }>
  >([]);
  const [adaptiveModeQuestion, setAdaptiveModeQuestion] = useState<string>(
    "Did you understand this concept?",
  );
  const [adaptiveDecision, setAdaptiveDecision] = useState<null | boolean>(null);
  const saveTimerRef = useRef<number | null>(null);

  const { analytics, recordInteraction, recordExperiment, recordQuizResult, clearAnalytics } =
    useLawLabAnalytics(law, learningMode);

  const currentModeCopy = MODE_COPY[learningMode];
  const currentQuiz = quiz[quizIndex] ?? quiz[0];
  const selectedExperiment = useMemo(
    () => savedExperiments.find((item) => item.id === selectedExperimentId) ?? null,
    [savedExperiments, selectedExperimentId],
  );

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    const storedScale = window.localStorage.getItem(`laws-of-motion-ui-scale:${law}`);
    const storedMotion = window.localStorage.getItem(`laws-of-motion-reduced-motion:${law}`);
    const storedSafe = window.localStorage.getItem(`laws-of-motion-color-safe:${law}`);
    if (storedScale) setUiScale(Number.parseFloat(storedScale) || 1);
    if (storedMotion) setReducedMotion(storedMotion === "true");
    if (storedSafe) setColorSafePalette(storedSafe === "true");
  }, [law]);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    window.localStorage.setItem(`laws-of-motion-ui-scale:${law}`, String(uiScale));
  }, [law, uiScale]);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    window.localStorage.setItem(`laws-of-motion-reduced-motion:${law}`, String(reducedMotion));
  }, [law, reducedMotion]);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    window.localStorage.setItem(`laws-of-motion-color-safe:${law}`, String(colorSafePalette));
  }, [law, colorSafePalette]);

  useEffect(() => {
    const data = fallbackQuiz(law);
    setQuiz(data);
    setQuizIndex(0);
    setQuizAnswer("");
    setQuizFeedback(null);
    setQuizHintVisible(false);
    setDragPairs({});
    setDragChoice(null);
  }, [law, learningMode]);

  useEffect(() => {
    const sample = {
      t: snapshot.time ?? Date.now() / 1000,
      force: parseStat(snapshot.stats, "Force") ?? config.controls.force,
      mass: parseStat(snapshot.stats, "Mass") ?? config.controls.mass,
      acceleration:
        parseStat(snapshot.stats, "Acceleration") ??
        config.controls.force / Math.max(1, config.controls.mass),
      velocity: parseStat(snapshot.stats, "Velocity") ?? config.controls.speed,
      momentum:
        parseStat(snapshot.stats, "Momentum") ?? config.controls.force * config.controls.mass,
      friction: parseStat(snapshot.stats, "Friction") ?? config.controls.friction,
    };

    setTimeline((current) => {
      const previous = current[current.length - 1];
      if (previous && Math.abs(previous.t - sample.t) < 0.12) {
        return current;
      }

      return [...current.slice(-71), sample];
    });
  }, [
    config.controls.force,
    config.controls.friction,
    config.controls.mass,
    config.controls.speed,
    snapshot.stats,
    snapshot.time,
  ]);

  useEffect(() => {
    const timer = saveTimerRef.current;
    if (!challengeActive || timer) {
      return;
    }

    const startedAt = Date.now();
    setChallengeStartedAt(startedAt);
    setChallengeRemaining(challenge.timerSeconds);

    saveTimerRef.current = window.setInterval(() => {
      setChallengeRemaining((current) => {
        if (current <= 1) {
          window.clearInterval(saveTimerRef.current as number);
          saveTimerRef.current = null;
          const elapsed = Math.max(0, Math.round((Date.now() - startedAt) / 1000));
          const score = scoreChallenge(law, config, snapshot, challenge, elapsed);
          setChallengeScore(score);
          recordExperiment();
          return 0;
        }

        return current - 1;
      });
    }, 1000);
  }, [challenge, challengeActive, config, law, recordExperiment, snapshot]);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    window.localStorage.setItem(
      `laws-of-motion-experiments:${law}`,
      JSON.stringify(savedExperiments.slice(0, 12)),
    );
  }, [law, savedExperiments]);

  useEffect(() => {
    setChallenge(challengeTemplate(law));
    setChallengeRemaining(challengeTemplate(law).timerSeconds);
  }, [law]);

  useEffect(() => {
    let active = true;

    const loadStructuredContent = async () => {
      try {
        const [quizResponse, challengeResponse, whatIfResponse] = await Promise.all([
          lawsOfMotionService.generateQuiz(law, learningMode, config.explanation),
          lawsOfMotionService.generateChallenge(law, learningMode, config.explanation),
          lawsOfMotionService.analyzeLearning(law, {
            timeSpentSeconds: analytics.timeSpentSeconds,
            interactions: analytics.interactions,
            experimentsCompleted: analytics.experimentsCompleted,
            quizAccuracy: analytics.quizAccuracy,
            mode: learningMode,
          }),
        ]);

        if (!active) {
          return;
        }

        if (quizResponse.success && quizResponse.quiz && quizResponse.quiz.length > 0) {
          setQuiz(quizResponse.quiz);
        }

        if (challengeResponse.success && challengeResponse.challenge) {
          setChallenge(challengeResponse.challenge);
          setChallengeRemaining(challengeResponse.challenge.timerSeconds);
        }

        if (whatIfResponse.success && whatIfResponse.analytics) {
          // Analysis only; the UI uses the values below.
          void whatIfResponse.analytics;
        }
      } catch {
        if (!active) {
          return;
        }

        setQuiz(fallbackQuiz(law));
        setChallenge(challengeTemplate(law));
      }
    };

    loadStructuredContent();

    return () => {
      active = false;
    };
  }, [
    analytics.experimentsCompleted,
    analytics.interactions,
    analytics.quizAccuracy,
    analytics.timeSpentSeconds,
    config.explanation,
    law,
    learningMode,
  ]);

  const chartColorSet = colorSafePalette
    ? ["#22d3ee", "#f59e0b", "#38bdf8", "#f472b6"]
    : ["#22d3ee", "#a855f7", "#38bdf8", "#f472b6"];

  const chartData = timeline.map((item, index) => ({
    ...item,
    t: Number((item.t - (timeline[0]?.t ?? item.t)).toFixed(2)),
    label: index + 1,
  }));

  const quizCurrent = quiz[quizIndex] ?? quiz[0];

  const handleSaveExperiment = () => {
    const next = createExperimentRecord(law, config, learningMode);
    setSavedExperiments((current) =>
      [next, ...current.filter((item) => item.id !== next.id)].slice(0, 10),
    );
    recordExperiment();
  };

  const handleReplayExperiment = (experiment: StoredExperiment) => {
    onApplyConfig(experiment.config);
    onLearningModeChange(experiment.learningMode);
    setSelectedExperimentId(experiment.id);
    recordInteraction("replay experiment");
  };

  const handleExportExperiment = (experiment: StoredExperiment) => {
    const blob = new Blob([JSON.stringify(experiment, null, 2)], { type: "application/json" });
    const url = window.URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `${experiment.label.replace(/[^a-z0-9]+/gi, "-").toLowerCase()}.json`;
    anchor.click();
    window.URL.revokeObjectURL(url);
    recordInteraction("export experiment");
  };

  const handleQuizSubmit = () => {
    if (!quizCurrent) {
      return;
    }

    let answer = quizAnswer.trim();
    if (quizCurrent.type === "drag-drop") {
      answer = Object.entries(dragPairs)
        .map(([key, value]) => `${key}: ${value}`)
        .join(" | ");
    }

    const correct =
      answer.toLowerCase().includes(quizCurrent.correctAnswer.toLowerCase()) ||
      answer === quizCurrent.correctAnswer;
    setQuizFeedback({
      answer: answer || "No answer provided.",
      correct,
      explanation: quizCurrent.explanation,
    });
    recordQuizResult(correct, quizCurrent.concept);
    if (!correct) {
      onLearningModeChange("formula");
    }
  };

  const handleNextQuiz = () => {
    setQuizIndex((current) => (current + 1) % quiz.length);
    setQuizAnswer("");
    setQuizFeedback(null);
    setQuizHintVisible(false);
    setDragPairs({});
    setDragChoice(null);
  };

  const handleWhatIf = async (customPrompt?: string) => {
    const promptText = customPrompt ?? whatIfPrompt;
    if (!promptText.trim()) {
      return;
    }

    setWhatIfLoading(true);
    try {
      const response = await lawsOfMotionService.explainWhatIf(
        law,
        promptText,
        learningMode,
        config.explanation,
      );
      if (response.success && response.whatIf) {
        const next = response.whatIf;
        setWhatIfAnswer(`${next.explanation} ${next.predictedOutcome}`);
        onLearningModeChange(next.recommendedMode);
      } else {
        const fallback = buildWhatIfPrompt(promptText, law);
        setWhatIfAnswer(`${fallback.explanation} ${fallback.predictedOutcome}`);
        onLearningModeChange(fallback.recommendedMode);
      }
    } catch {
      const fallback = buildWhatIfPrompt(promptText, law);
      setWhatIfAnswer(`${fallback.explanation} ${fallback.predictedOutcome}`);
      onLearningModeChange(fallback.recommendedMode);
    } finally {
      setWhatIfLoading(false);
    }
    recordInteraction("what if query");
  };

  const handleAdaptiveCheck = (understood: boolean) => {
    setAdaptiveDecision(understood);
    if (understood) {
      recordInteraction("concept understood");
      return;
    }

    recordInteraction("concept struggled");
    onLearningModeChange(analytics.recommendedMode);
    setAdaptiveModeQuestion("Try this simplified version: what changes first in the scene?");
  };

  const modeRecommendation =
    analytics.recommendedMode === learningMode
      ? modeLabel(learningMode)
      : modeLabel(analytics.recommendedMode);
  const modePrompt = currentModeCopy.focus;

  return (
    <section className="mt-6 space-y-4">
      <div
        className="glass-strong rounded-3xl border border-white/10 p-5"
        style={{ transform: `scale(${uiScale})`, transformOrigin: "top left" }}
      >
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="space-y-3">
            <div className="inline-flex items-center gap-2 rounded-full border border-[var(--neon-cyan)]/20 bg-[var(--neon-cyan)]/10 px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.35em] text-[var(--neon-cyan)]">
              <Sparkles className="h-3.5 w-3.5" /> {title} · Adaptive learning layer
            </div>
            <h2 className="text-2xl font-bold text-white">
              Mode-aware tutoring, challenge flow, analytics, and experiment history
            </h2>
            <p className="max-w-3xl text-sm text-slate-300">{modePrompt}</p>
            <div className="flex flex-wrap gap-2 text-[11px] text-slate-200">
              <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1">
                Overlay: {currentModeCopy.overlay}
              </span>
              <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1">
                Tutorial flow: {currentModeCopy.tutorial}
              </span>
              <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1">
                Hint: {currentModeCopy.hint}
              </span>
            </div>
          </div>
          <div className="grid gap-2 sm:grid-cols-2 lg:w-[360px]">
            <MetricTile
              icon={<Clock3 className="h-4 w-4" />}
              label="Time spent"
              value={formatSeconds(analytics.timeSpentSeconds)}
              accent="text-[var(--neon-cyan)]"
            />
            <MetricTile
              icon={<Activity className="h-4 w-4" />}
              label="Interactions"
              value={String(analytics.interactions)}
              accent="text-[var(--neon-purple)]"
            />
            <MetricTile
              icon={<ShieldCheck className="h-4 w-4" />}
              label="Experiments"
              value={String(analytics.experimentsCompleted)}
              accent="text-[var(--neon-blue)]"
            />
            <MetricTile
              icon={<BadgeCheck className="h-4 w-4" />}
              label="Quiz accuracy"
              value={`${analytics.quizAccuracy}%`}
              accent="text-[var(--neon-cyan)]"
            />
          </div>
        </div>

        <div className="mt-5 grid gap-4 xl:grid-cols-[320px_minmax(0,1fr)_320px]">
          <div className="space-y-4">
            <LearningModePicker mode={learningMode} onChange={onLearningModeChange} />

            <div className="glass rounded-3xl border border-white/10 p-4 space-y-3">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <div className="text-xs uppercase tracking-[0.3em] text-[var(--neon-cyan)]">
                    Adaptive check-in
                  </div>
                  <h3 className="text-lg font-semibold text-white">
                    Did you understand this concept?
                  </h3>
                </div>
                <Lightbulb className="h-5 w-5 text-[var(--neon-cyan)]" />
              </div>
              <div className="flex gap-2">
                <Button
                  onClick={() => handleAdaptiveCheck(true)}
                  variant="outline"
                  className="border-white/10 bg-white/5 text-foreground hover:bg-white/10"
                >
                  Yes
                </Button>
                <Button
                  onClick={() => handleAdaptiveCheck(false)}
                  className="bg-gradient-to-r from-[var(--neon-cyan)] to-[var(--neon-blue)] text-slate-950"
                >
                  Not yet
                </Button>
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/5 p-3 text-xs text-slate-200">
                {adaptiveDecision === null
                  ? "The tutor will adapt once you answer."
                  : adaptiveDecision
                    ? "Good. Keep exploring the challenge and try a different learning mode if you want more depth."
                    : adaptiveModeQuestion}
              </div>
              <div className="flex flex-wrap gap-2 text-[11px]">
                <button
                  className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-slate-200"
                  onClick={() => onLearningModeChange("real-life")}
                >
                  Show real-life example
                </button>
                <button
                  className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-slate-200"
                  onClick={() => onLearningModeChange("interactive")}
                >
                  Guided experiment
                </button>
                <button
                  className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-slate-200"
                  onClick={() => onLearningModeChange("formula")}
                >
                  Simplify formula
                </button>
              </div>
            </div>

            <div className="glass rounded-3xl border border-white/10 p-4 space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-xs uppercase tracking-[0.3em] text-[var(--neon-cyan)]">
                    Accessibility
                  </div>
                  <h3 className="text-lg font-semibold text-white">Readable, reduced-motion UI</h3>
                </div>
                <ShieldCheck className="h-5 w-5 text-[var(--neon-cyan)]" />
              </div>
              <ToggleRow
                label="Reduced motion"
                checked={reducedMotion}
                onChange={setReducedMotion}
              />
              <ToggleRow
                label="Colorblind-safe palette"
                checked={colorSafePalette}
                onChange={setColorSafePalette}
              />
              <label className="space-y-2 text-sm text-slate-200">
                <div className="flex items-center justify-between text-xs uppercase tracking-[0.3em] text-muted-foreground">
                  <span>UI scale</span>
                  <span className="font-mono text-[var(--neon-cyan)]">{uiScale.toFixed(2)}x</span>
                </div>
                <input
                  type="range"
                  min="0.9"
                  max="1.2"
                  step="0.05"
                  value={uiScale}
                  onChange={(event) => setUiScale(Number(event.target.value))}
                  className="w-full accent-[var(--neon-cyan)]"
                />
              </label>
              <div className="rounded-2xl border border-white/10 bg-white/5 p-3 text-xs text-slate-200">
                Keyboard shortcuts: Space pauses, R resets, C captures a challenge attempt, and H
                saves the current experiment.
              </div>
            </div>

            <div className="glass rounded-3xl border border-white/10 p-4 space-y-3">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <div className="text-xs uppercase tracking-[0.3em] text-[var(--neon-cyan)]">
                    Quick actions
                  </div>
                  <h3 className="text-lg font-semibold text-white">Engine shortcuts</h3>
                </div>
                <RefreshCw className="h-5 w-5 text-[var(--neon-cyan)]" />
              </div>
              <div className="grid grid-cols-2 gap-2">
                {engineActions.map((action) => (
                  <motion.button
                    key={action.label}
                    whileHover={reducedMotion ? undefined : { y: -2 }}
                    whileTap={reducedMotion ? undefined : { scale: 0.98 }}
                    onClick={() => {
                      recordInteraction(action.label);
                      action.onClick();
                    }}
                    className="flex items-center justify-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-3 py-3 text-sm text-slate-200 transition hover:bg-white/10"
                    aria-label={action.label}
                  >
                    {action.icon}
                    {action.label}
                  </motion.button>
                ))}
              </div>
              {recommendedPath && recommendedPath.length > 0 ? (
                <div className="rounded-2xl border border-white/10 bg-white/5 p-3 text-xs text-slate-200">
                  <div className="mb-2 text-[10px] uppercase tracking-[0.3em] text-[var(--neon-cyan)]">
                    Recommended path
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {recommendedPath.map((item) => (
                      <span
                        key={item}
                        className="rounded-full border border-white/10 bg-black/20 px-3 py-1 text-[11px]"
                      >
                        {item}
                      </span>
                    ))}
                  </div>
                </div>
              ) : null}
            </div>
          </div>

          <div className="space-y-4">
            <div className="glass rounded-3xl border border-white/10 p-4 space-y-3">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <div className="text-xs uppercase tracking-[0.3em] text-[var(--neon-cyan)]">
                    Live graphs
                  </div>
                  <h3 className="text-lg font-semibold text-white">
                    Velocity, acceleration, force, momentum
                  </h3>
                </div>
                <Activity className="h-5 w-5 text-[var(--neon-cyan)]" />
              </div>
              <div className="grid gap-3 xl:grid-cols-2">
                <MiniChart
                  title="Velocity vs time"
                  data={chartData}
                  dataKey="velocity"
                  stroke={chartColorSet[0]}
                />
                <MiniChart
                  title="Acceleration vs time"
                  data={chartData}
                  dataKey="acceleration"
                  stroke={chartColorSet[1]}
                />
                <MiniChart
                  title="Force vs time"
                  data={chartData}
                  dataKey="force"
                  stroke={chartColorSet[2]}
                />
                <MiniChart
                  title="Momentum vs time"
                  data={chartData}
                  dataKey="momentum"
                  stroke={chartColorSet[3]}
                />
              </div>
            </div>

            <div className="grid gap-4 lg:grid-cols-2">
              <div className="glass rounded-3xl border border-white/10 p-4 space-y-3">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <div className="text-xs uppercase tracking-[0.3em] text-[var(--neon-cyan)]">
                      AI tutor
                    </div>
                    <h3 className="text-lg font-semibold text-white">
                      Contextual explanations and follow-ups
                    </h3>
                  </div>
                  <Sparkles className="h-5 w-5 text-[var(--neon-cyan)]" />
                </div>
                <TutorCard
                  title={`${lawFriendlyName(law)} tutor`}
                  subtitle="Ask why the system changed, then let the tutor adapt to your learning mode."
                  response={tutorAnswer || snapshot.hint || config.explanation}
                  question={tutorQuestion}
                  setQuestion={setTutorQuestion}
                  onAsk={onAskTutor}
                  askLoading={tutorLoading}
                  hints={
                    tutorInsights?.recommendations?.length
                      ? tutorInsights.recommendations
                      : config.tutorHints
                  }
                  insights={tutorInsights}
                  followUpLabel="Follow-up questions"
                />
              </div>

              <div className="glass rounded-3xl border border-white/10 p-4 space-y-3">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <div className="text-xs uppercase tracking-[0.3em] text-[var(--neon-cyan)]">
                      What if?
                    </div>
                    <h3 className="text-lg font-semibold text-white">
                      Ask a hypothetical question
                    </h3>
                  </div>
                  <Wand2 className="h-5 w-5 text-[var(--neon-cyan)]" />
                </div>
                <Textarea
                  value={whatIfPrompt}
                  onChange={(event) => setWhatIfPrompt(event.target.value)}
                  className="min-h-24 resize-none border-white/10 bg-white/5 text-white placeholder:text-white/30"
                  placeholder="What if gravity becomes zero?"
                />
                <div className="flex flex-wrap gap-2">
                  {[
                    "What if gravity becomes zero?",
                    "What if mass doubles?",
                    "What if friction disappears?",
                  ].map((example) => (
                    <button
                      key={example}
                      className="rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-slate-200 hover:bg-white/10"
                      onClick={() => void handleWhatIf(example)}
                    >
                      {example}
                    </button>
                  ))}
                </div>
                <Button
                  onClick={() => void handleWhatIf()}
                  disabled={whatIfLoading}
                  className="w-full bg-gradient-to-r from-[var(--neon-purple)] to-[var(--neon-blue)] text-white"
                >
                  {whatIfLoading ? "Analyzing..." : "Explain what if"}
                </Button>
                <div className="rounded-2xl border border-white/10 bg-black/20 p-3 text-sm text-slate-200 min-h-24 whitespace-pre-line">
                  {whatIfAnswer || "The tutor will explain the outcome dynamically."}
                </div>
              </div>
            </div>

            <div className="glass rounded-3xl border border-white/10 p-4 space-y-3">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <div className="text-xs uppercase tracking-[0.3em] text-[var(--neon-cyan)]">
                    Quiz system
                  </div>
                  <h3 className="text-lg font-semibold text-white">
                    MCQs, predictions, drag and drop
                  </h3>
                </div>
                <Trophy className="h-5 w-5 text-[var(--neon-cyan)]" />
              </div>
              {quizCurrent ? (
                <div className="space-y-3">
                  <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                    <div className="text-[10px] uppercase tracking-[0.3em] text-[var(--neon-cyan)]">
                      Question {quizIndex + 1} of {quiz.length}
                    </div>
                    <div className="mt-2 text-sm text-white">{quizCurrent.prompt}</div>
                    {quizCurrent.type === "mcq" && quizCurrent.options ? (
                      <div className="mt-3 grid gap-2">
                        {quizCurrent.options.map((option) => (
                          <button
                            key={option}
                            onClick={() => setQuizAnswer(option)}
                            className={cn(
                              "rounded-2xl border px-3 py-2 text-left text-sm transition",
                              quizAnswer === option
                                ? "border-[var(--neon-cyan)]/60 bg-[var(--neon-cyan)]/10 text-white"
                                : "border-white/10 bg-white/5 text-slate-200 hover:bg-white/10",
                            )}
                          >
                            {option}
                          </button>
                        ))}
                      </div>
                    ) : null}
                    {quizCurrent.type === "prediction" ? (
                      <Textarea
                        value={quizAnswer}
                        onChange={(event) => setQuizAnswer(event.target.value)}
                        className="mt-3 min-h-24 resize-none border-white/10 bg-white/5 text-white placeholder:text-white/30"
                        placeholder="Type your prediction here..."
                      />
                    ) : null}
                    {quizCurrent.type === "drag-drop" ? (
                      <div className="mt-3 grid gap-3 md:grid-cols-2">
                        <div className="space-y-2">
                          <div className="text-xs uppercase tracking-[0.3em] text-muted-foreground">
                            Drag items
                          </div>
                          <div className="flex flex-wrap gap-2">
                            {(quizCurrent.dragItems || []).map((item) => (
                              <button
                                key={item}
                                draggable
                                onDragStart={() => setDragChoice(item)}
                                className={cn(
                                  "inline-flex items-center gap-2 rounded-full border px-3 py-2 text-xs transition",
                                  dragChoice === item
                                    ? "border-[var(--neon-cyan)]/60 bg-[var(--neon-cyan)]/10 text-white"
                                    : "border-white/10 bg-white/5 text-slate-200",
                                )}
                              >
                                <GripVertical className="h-3.5 w-3.5" />
                                {item}
                              </button>
                            ))}
                          </div>
                        </div>
                        <div className="space-y-2">
                          <div className="text-xs uppercase tracking-[0.3em] text-muted-foreground">
                            Drop targets
                          </div>
                          <div className="grid gap-2">
                            {(quizCurrent.dropTargets || []).map((target) => (
                              <button
                                key={target}
                                onDragOver={(event) => event.preventDefault()}
                                onDrop={(event) => {
                                  event.preventDefault();
                                  if (!dragChoice) {
                                    return;
                                  }
                                  setDragPairs((current) => ({ ...current, [dragChoice]: target }));
                                }}
                                className="rounded-2xl border border-dashed border-white/15 bg-white/5 px-3 py-3 text-left text-xs text-slate-200"
                              >
                                {target}
                                <span className="mt-1 block text-[10px] uppercase tracking-[0.3em] text-muted-foreground">
                                  Drop matching item here
                                </span>
                              </button>
                            ))}
                          </div>
                          <div className="rounded-2xl border border-white/10 bg-black/20 p-3 text-xs text-slate-200">
                            Current matches:{" "}
                            {Object.entries(dragPairs)
                              .map(([key, value]) => `${key} → ${value}`)
                              .join(" · ") || "none yet"}
                          </div>
                        </div>
                      </div>
                    ) : null}
                    <div className="mt-3 flex flex-wrap gap-2">
                      <Button
                        onClick={handleQuizSubmit}
                        className="bg-gradient-to-r from-[var(--neon-cyan)] to-[var(--neon-blue)] text-slate-950"
                      >
                        Submit
                      </Button>
                      <Button
                        variant="outline"
                        className="border-white/10 bg-white/5 text-foreground hover:bg-white/10"
                        onClick={handleNextQuiz}
                      >
                        Next
                      </Button>
                      <Button
                        variant="outline"
                        className="border-white/10 bg-white/5 text-foreground hover:bg-white/10"
                        onClick={() => setQuizHintVisible((current) => !current)}
                      >
                        Hint
                      </Button>
                    </div>
                    {quizHintVisible ? (
                      <div className="mt-3 rounded-2xl border border-white/10 bg-white/5 p-3 text-xs text-slate-200">
                        {quizCurrent.hint}
                      </div>
                    ) : null}
                    {quizFeedback ? (
                      <div
                        className={cn(
                          "mt-3 rounded-2xl border p-3 text-xs",
                          quizFeedback.correct
                            ? "border-emerald-400/20 bg-emerald-400/5 text-emerald-100"
                            : "border-amber-400/20 bg-amber-400/5 text-amber-50",
                        )}
                      >
                        <div className="mb-1 text-[10px] uppercase tracking-[0.3em]">
                          {quizFeedback.correct ? "Correct" : "Try again"}
                        </div>
                        <div>{quizFeedback.explanation}</div>
                        <div className="mt-2 text-[11px] text-slate-200">
                          Your answer: {quizFeedback.answer}
                        </div>
                      </div>
                    ) : null}
                  </div>
                </div>
              ) : (
                <div className="rounded-2xl border border-dashed border-white/10 bg-white/5 p-4 text-sm text-slate-300">
                  Loading quiz content...
                </div>
              )}
            </div>
          </div>

          <div className="space-y-4">
            <div className="glass rounded-3xl border border-white/10 p-4 space-y-3">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <div className="text-xs uppercase tracking-[0.3em] text-[var(--neon-cyan)]">
                    Performance analytics
                  </div>
                  <h3 className="text-lg font-semibold text-white">Progress and mastery</h3>
                </div>
                <Star className="h-5 w-5 text-[var(--neon-cyan)]" />
              </div>
              <ProgressBar label="Completion" value={analytics.progressPercent} />
              <ProgressBar label="Quiz accuracy" value={analytics.quizAccuracy} />
              <div className="grid gap-2 text-xs text-slate-200">
                <StatChip label="Strengths" value={analytics.strengths.join(" · ")} />
                <StatChip
                  label="Weaknesses"
                  value={analytics.weaknesses.join(" · ") || "None identified yet"}
                />
                <StatChip label="Recommended mode" value={modeRecommendation} />
              </div>
              <div className="flex gap-2 flex-wrap">
                <Button
                  variant="outline"
                  className="border-white/10 bg-white/5 text-foreground hover:bg-white/10"
                  onClick={clearAnalytics}
                >
                  Clear analytics
                </Button>
              </div>
            </div>

            <div className="glass rounded-3xl border border-white/10 p-4 space-y-3">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <div className="text-xs uppercase tracking-[0.3em] text-[var(--neon-cyan)]">
                    Challenge mode
                  </div>
                  <h3 className="text-lg font-semibold text-white">Score, timer, badges</h3>
                </div>
                <Trophy className="h-5 w-5 text-[var(--neon-cyan)]" />
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/5 p-3 text-sm text-slate-200">
                <div className="font-semibold text-white">{challenge.title}</div>
                <div className="mt-1 text-xs text-slate-300">{challenge.objective}</div>
                <div className="mt-2 flex items-center gap-2 text-[11px] text-slate-200">
                  <Clock3 className="h-3.5 w-3.5 text-[var(--neon-cyan)]" />{" "}
                  {challengeActive
                    ? formatSeconds(challengeRemaining)
                    : `${challenge.timerSeconds}s`}
                </div>
              </div>
              <div className="flex gap-2 flex-wrap">
                <Button
                  onClick={() => {
                    setChallengeActive(true);
                    setChallengeScore(null);
                  }}
                  className="bg-gradient-to-r from-[var(--neon-purple)] to-[var(--neon-blue)] text-white"
                >
                  <Play className="mr-2 h-4 w-4" /> Start
                </Button>
                <Button
                  onClick={() => {
                    if (challengeStartedAt) {
                      const elapsed = Math.max(
                        0,
                        Math.round((Date.now() - challengeStartedAt) / 1000),
                      );
                      setChallengeScore(scoreChallenge(law, config, snapshot, challenge, elapsed));
                      recordExperiment();
                      setChallengeActive(false);
                    }
                  }}
                  variant="outline"
                  className="border-white/10 bg-white/5 text-foreground hover:bg-white/10"
                >
                  <Pause className="mr-2 h-4 w-4" /> Submit
                </Button>
                <Button
                  onClick={() => {
                    setChallengeActive(false);
                    setChallengeScore(null);
                    setChallengeRemaining(challenge.timerSeconds);
                  }}
                  variant="outline"
                  className="border-white/10 bg-white/5 text-foreground hover:bg-white/10"
                >
                  <TimerReset className="mr-2 h-4 w-4" /> Reset
                </Button>
              </div>
              {challengeScore !== null ? (
                <div className="rounded-2xl border border-[var(--neon-cyan)]/20 bg-[var(--neon-cyan)]/5 p-3 text-sm text-slate-200">
                  <div className="text-[10px] uppercase tracking-[0.3em] text-[var(--neon-cyan)]">
                    Score
                  </div>
                  <div className="mt-1 text-2xl font-bold text-white">{challengeScore}/100</div>
                  <div className="mt-1 text-xs text-slate-300">
                    Badges: {challenge.badges.join(" · ")}
                  </div>
                </div>
              ) : null}
              <div className="space-y-2">
                {challenge.scoringGuide.map((item) => (
                  <div
                    key={item}
                    className="rounded-2xl border border-white/10 bg-white/5 px-3 py-2 text-xs text-slate-200"
                  >
                    {item}
                  </div>
                ))}
              </div>
            </div>

            <div className="glass rounded-3xl border border-white/10 p-4 space-y-3">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <div className="text-xs uppercase tracking-[0.3em] text-[var(--neon-cyan)]">
                    Experiment history
                  </div>
                  <h3 className="text-lg font-semibold text-white">
                    Save, replay, compare, export
                  </h3>
                </div>
                <History className="h-5 w-5 text-[var(--neon-cyan)]" />
              </div>
              <div className="flex flex-wrap gap-2">
                <Button
                  onClick={handleSaveExperiment}
                  className="bg-gradient-to-r from-[var(--neon-cyan)] to-[var(--neon-blue)] text-slate-950"
                >
                  <Save className="mr-2 h-4 w-4" /> Save current
                </Button>
                <Button
                  variant="outline"
                  className="border-white/10 bg-white/5 text-foreground hover:bg-white/10"
                  onClick={() => setSavedExperiments([])}
                >
                  Clear history
                </Button>
              </div>
              <div className="space-y-2 max-h-80 overflow-auto pr-1">
                {savedExperiments.length === 0 ? (
                  <div className="rounded-2xl border border-dashed border-white/10 bg-white/5 p-3 text-xs text-slate-300">
                    Saved experiments appear here. Capture a setup and replay it later.
                  </div>
                ) : (
                  savedExperiments.map((experiment) => (
                    <button
                      key={experiment.id}
                      onClick={() => setSelectedExperimentId(experiment.id)}
                      className={cn(
                        "w-full rounded-2xl border p-3 text-left transition",
                        selectedExperimentId === experiment.id
                          ? "border-[var(--neon-cyan)]/50 bg-[var(--neon-cyan)]/10"
                          : "border-white/10 bg-white/5 hover:bg-white/10",
                      )}
                    >
                      <div className="flex items-center justify-between gap-3">
                        <div>
                          <div className="text-sm font-semibold text-white">{experiment.label}</div>
                          <div className="text-[11px] uppercase tracking-[0.3em] text-slate-300">
                            {new Date(experiment.savedAt).toLocaleString()}
                          </div>
                        </div>
                        <div className="flex items-center gap-2 text-[11px] text-slate-300">
                          <button
                            className="rounded-full border border-white/10 bg-black/20 px-2 py-1"
                            onClick={(event) => {
                              event.stopPropagation();
                              handleReplayExperiment(experiment);
                            }}
                          >
                            Replay
                          </button>
                          <button
                            className="rounded-full border border-white/10 bg-black/20 px-2 py-1"
                            onClick={(event) => {
                              event.stopPropagation();
                              handleExportExperiment(experiment);
                            }}
                          >
                            Export
                          </button>
                        </div>
                      </div>
                    </button>
                  ))
                )}
              </div>
              {selectedExperiment ? (
                <div className="rounded-2xl border border-white/10 bg-black/20 p-3 text-xs text-slate-200">
                  <div className="mb-2 text-[10px] uppercase tracking-[0.3em] text-[var(--neon-cyan)]">
                    Selected experiment
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <StatChip label="Law" value={selectedExperiment.law} />
                    <StatChip label="Mode" value={modeLabel(selectedExperiment.learningMode)} />
                  </div>
                </div>
              ) : null}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function MetricTile({
  icon,
  label,
  value,
  accent,
}: {
  icon: ReactNode;
  label: string;
  value: string;
  accent: string;
}) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-3">
      <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.3em] text-muted-foreground">
        {icon}
        <span>{label}</span>
      </div>
      <div className={cn("mt-1 text-xl font-bold", accent)}>{value}</div>
    </div>
  );
}

function ProgressBar({ label, value }: { label: string; value: number }) {
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs uppercase tracking-[0.3em] text-muted-foreground">
        <span>{label}</span>
        <span>{value}%</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-white/10">
        <div
          className="h-full rounded-full bg-gradient-to-r from-[var(--neon-cyan)] to-[var(--neon-blue)]"
          style={{ width: `${Math.max(0, Math.min(100, value))}%` }}
        />
      </div>
    </div>
  );
}

function StatChip({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 px-3 py-2">
      <div className="text-[10px] uppercase tracking-[0.3em] text-muted-foreground">{label}</div>
      <div className="mt-1 text-xs text-slate-200">{value}</div>
    </div>
  );
}

function ToggleRow({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (value: boolean) => void;
}) {
  return (
    <label className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-slate-200">
      <span>{label}</span>
      <input
        type="checkbox"
        checked={checked}
        onChange={(event) => onChange(event.target.checked)}
        className="h-4 w-4 accent-[var(--neon-cyan)]"
      />
    </label>
  );
}

function MiniChart({
  title,
  data,
  dataKey,
  stroke,
}: {
  title: string;
  data: Array<Record<string, number>>;
  dataKey: string;
  stroke: string;
}) {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-3">
      <div className="mb-2 text-xs uppercase tracking-[0.3em] text-muted-foreground">{title}</div>
      <div className="h-40">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid stroke="rgba(255,255,255,0.08)" strokeDasharray="3 3" />
            <XAxis
              dataKey="t"
              tick={{ fill: "#cbd5e1", fontSize: 10 }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis tick={{ fill: "#cbd5e1", fontSize: 10 }} axisLine={false} tickLine={false} />
            <Tooltip
              contentStyle={{
                background: "rgba(2, 6, 23, 0.95)",
                border: "1px solid rgba(255,255,255,0.12)",
                borderRadius: 16,
                color: "#fff",
              }}
              labelStyle={{ color: "#22d3ee" }}
            />
            <Line
              type="monotone"
              dataKey={dataKey}
              stroke={stroke}
              strokeWidth={2.4}
              dot={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
