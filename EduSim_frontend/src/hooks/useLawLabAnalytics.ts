import { useEffect, useMemo, useRef, useState } from "react";
import type { LawKey, LearningMode } from "@/types/lawsOfMotion";

type StoredLawAnalytics = {
  timeSpentSeconds: number;
  interactions: number;
  experimentsCompleted: number;
  quizCorrect: number;
  quizTotal: number;
  struggledConcepts: Record<string, number>;
};

const DEFAULT_ANALYTICS: StoredLawAnalytics = {
  timeSpentSeconds: 0,
  interactions: 0,
  experimentsCompleted: 0,
  quizCorrect: 0,
  quizTotal: 0,
  struggledConcepts: {},
};

function storageKey(law: LawKey) {
  return `laws-of-motion-analytics:${law}`;
}

function loadAnalytics(law: LawKey): StoredLawAnalytics {
  if (typeof window === "undefined") {
    return DEFAULT_ANALYTICS;
  }

  const saved = window.localStorage.getItem(storageKey(law));
  if (!saved) {
    return DEFAULT_ANALYTICS;
  }

  try {
    return { ...DEFAULT_ANALYTICS, ...JSON.parse(saved) } as StoredLawAnalytics;
  } catch {
    return DEFAULT_ANALYTICS;
  }
}

function saveAnalytics(law: LawKey, analytics: StoredLawAnalytics) {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(storageKey(law), JSON.stringify(analytics));
}

function inferRecommendedMode(
  analytics: StoredLawAnalytics,
  currentMode: LearningMode,
): LearningMode {
  const accuracy = analytics.quizTotal > 0 ? analytics.quizCorrect / analytics.quizTotal : 1;
  const struggleCount = Object.values(analytics.struggledConcepts).reduce(
    (total, value) => total + value,
    0,
  );

  if (accuracy < 0.55 || struggleCount > 4) {
    return "formula";
  }

  if (analytics.interactions > 10 && accuracy >= 0.8) {
    return "gamified";
  }

  if (currentMode === "interactive" && analytics.interactions > 4) {
    return "real-life";
  }

  return currentMode;
}

export function useLawLabAnalytics(law: LawKey, currentMode: LearningMode) {
  const [analytics, setAnalytics] = useState<StoredLawAnalytics>(() => loadAnalytics(law));
  const liveStart = useRef(Date.now());

  useEffect(() => {
    liveStart.current = Date.now();
    setAnalytics(loadAnalytics(law));
  }, [law]);

  useEffect(() => {
    const interval = window.setInterval(() => {
      setAnalytics((current) => {
        const next = {
          ...current,
          timeSpentSeconds: current.timeSpentSeconds + 1,
        };
        saveAnalytics(law, next);
        return next;
      });
    }, 1000);

    return () => {
      window.clearInterval(interval);
      const elapsed = Math.max(0, Math.round((Date.now() - liveStart.current) / 1000));
      setAnalytics((current) => {
        const next = {
          ...current,
          timeSpentSeconds: Math.max(current.timeSpentSeconds, current.timeSpentSeconds + elapsed),
        };
        saveAnalytics(law, next);
        return next;
      });
    };
  }, [law]);

  const recordInteraction = (concept?: string) => {
    setAnalytics((current) => {
      const next = {
        ...current,
        interactions: current.interactions + 1,
        struggledConcepts:
          concept && concept.trim().length > 0
            ? {
                ...current.struggledConcepts,
                [concept]: (current.struggledConcepts[concept] || 0) + 1,
              }
            : current.struggledConcepts,
      };
      saveAnalytics(law, next);
      return next;
    });
  };

  const recordExperiment = () => {
    setAnalytics((current) => {
      const next = { ...current, experimentsCompleted: current.experimentsCompleted + 1 };
      saveAnalytics(law, next);
      return next;
    });
  };

  const recordQuizResult = (correct: boolean, concept: string) => {
    setAnalytics((current) => {
      const next = {
        ...current,
        quizCorrect: current.quizCorrect + (correct ? 1 : 0),
        quizTotal: current.quizTotal + 1,
        struggledConcepts: correct
          ? current.struggledConcepts
          : {
              ...current.struggledConcepts,
              [concept]: (current.struggledConcepts[concept] || 0) + 1,
            },
      };
      saveAnalytics(law, next);
      return next;
    });
  };

  const progressPercent = useMemo(() => {
    const accuracy = analytics.quizTotal > 0 ? analytics.quizCorrect / analytics.quizTotal : 0.5;
    const baseline =
      analytics.interactions * 4 + analytics.experimentsCompleted * 14 + accuracy * 40;
    return Math.max(10, Math.min(100, Math.round(baseline)));
  }, [analytics]);

  const quizAccuracy =
    analytics.quizTotal > 0 ? Math.round((analytics.quizCorrect / analytics.quizTotal) * 100) : 0;
  const strengths =
    analytics.interactions > 6
      ? ["Active experimentation", "Consistent slider interaction", "Steady concept recall"]
      : ["Focused observation", "Learning mode awareness"];

  const weaknesses = Object.entries(analytics.struggledConcepts)
    .sort((left, right) => right[1] - left[1])
    .slice(0, 3)
    .map(([concept]) => concept);

  return {
    analytics: {
      ...analytics,
      quizAccuracy,
      strengths,
      weaknesses,
      progressPercent,
      recommendedMode: inferRecommendedMode(analytics, currentMode),
    },
    recordInteraction,
    recordExperiment,
    recordQuizResult,
    clearAnalytics: () => {
      const next = { ...DEFAULT_ANALYTICS };
      saveAnalytics(law, next);
      setAnalytics(next);
    },
  };
}
