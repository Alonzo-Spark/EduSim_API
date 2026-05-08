/**
 * Tutor Page Route
 * AI-powered physics tutor for students
 */

import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { TutorInputPanel } from "@/components/tutor/TutorInputPanel";
import { TutorOutputPanel } from "@/components/tutor/TutorOutputPanel";
import { TutorService, TutorAnalysisResponse } from "@/services/TutorService";

export const Route = createFileRoute("/tutor")({
  component: TutorPage,
});

function TutorPage() {
  const [tutorData, setTutorData] = useState<TutorAnalysisResponse["data"] | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async (query: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await TutorService.analyzeQuery(query);
      if (response.success) {
        setTutorData(response.data);
      } else {
        setError("Failed to analyze question.");
      }
    } catch (err: any) {
      setError(err.message || "An error occurred while contacting the tutor service.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-8rem)] w-full text-white">
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gradient mb-2">AI Physics Tutor</h1>
        <p className="text-muted-foreground">Your intelligent companion for exploring physics concepts and formulas.</p>
      </div>

      {/* Main Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 h-[calc(100vh-14rem)]">
        {/* Left: Input Panel */}
        <div className="min-w-0 h-full">
          <TutorInputPanel onAnalyze={handleAnalyze} isLoading={isLoading} className="h-full" />
        </div>

        {/* Right: Output Panel */}
        <div className="min-w-0 h-full">
          <TutorOutputPanel data={tutorData} className="h-full" />
        </div>
      </div>

      {/* Global Error Toast */}
      {error && (
        <div className="fixed bottom-6 right-6 bg-red-500/10 border border-red-500/30 rounded-2xl p-4 max-w-md animate-in slide-in-from-right-8 glow-red">
          <p className="text-sm text-red-300 font-medium">{error}</p>
        </div>
      )}
    </div>
  );
}
