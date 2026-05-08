import React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Brain, Star, Target } from "lucide-react";

interface MasteryMetric {
  conceptual: number;
  practical: number;
  overall: number;
}

interface MasteryMapProps {
  mastery: Record<string, MasteryMetric>;
}

export const MasteryMap: React.FC<MasteryMapProps> = ({ mastery }) => {
  const topics = Object.keys(mastery);

  if (topics.length === 0) {
    return (
      <Card className="bg-slate-900/50 border-slate-800">
        <CardContent className="py-10 text-center">
          <Brain className="w-12 h-12 text-slate-700 mx-auto mb-4 opacity-20" />
          <p className="text-slate-500 italic">No mastery data yet. Start a simulation to begin!</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {topics.map((topic) => (
        <Card key={topic} className="bg-slate-900/80 border-slate-800 hover:border-indigo-500/50 transition-all group overflow-hidden">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-semibold flex items-center justify-between">
              <span className="truncate">{topic}</span>
              <Badge variant="outline" className="bg-indigo-500/10 text-indigo-400 border-indigo-500/20">
                {mastery[topic].overall}% Mastery
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <div className="flex justify-between text-[10px] uppercase text-slate-500 font-bold tracking-wider">
                <span className="flex items-center gap-1"><Brain className="w-3 h-3" /> Conceptual</span>
                <span>{mastery[topic].conceptual}%</span>
              </div>
              <Progress value={mastery[topic].conceptual} className="h-1.5 bg-slate-800" indicatorClassName="bg-gradient-to-r from-emerald-500 to-teal-400" />
            </div>

            <div className="space-y-2">
              <div className="flex justify-between text-[10px] uppercase text-slate-500 font-bold tracking-wider">
                <span className="flex items-center gap-1"><Target className="w-3 h-3" /> Practical</span>
                <span>{mastery[topic].practical}%</span>
              </div>
              <Progress value={mastery[topic].practical} className="h-1.5 bg-slate-800" indicatorClassName="bg-gradient-to-r from-sky-500 to-indigo-400" />
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
};

const Badge = ({ children, variant, className }: any) => (
  <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${className}`}>
    {children}
  </span>
);
