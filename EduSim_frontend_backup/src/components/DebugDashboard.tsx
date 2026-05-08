import React, { useState, useEffect } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Activity, AlertTriangle, Cpu, MousePointer2, Brain } from "lucide-react";


interface HealthScore {
  stability: number;
  interactivity: number;
  performance: number;
  overall: number;
}

export const DebugDashboard: React.FC = () => {
  const [logs, setLogs] = useState<any[]>([]);
  const [health, setHealth] = useState<HealthScore | null>(null);

  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      const { type, payload } = event.data;
      if (!type || !type.startsWith("sim_")) return;

      setLogs((prev) => [{ type, payload, time: new Date().toLocaleTimeString() }, ...prev].slice(0, 50));
      
      if (type === "sim_performance") {
        setHealth(h => ({
            stability: h?.stability || 100,
            interactivity: h?.interactivity || 0,
            performance: payload.fps ? Math.min(100, (payload.fps / 60) * 100) : (h?.performance || 0),
            overall: 0
        }));
      }
    };

    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, []);

  return (
    <div className="fixed bottom-4 right-4 w-80 max-h-[500px] overflow-y-auto z-50 flex flex-col gap-4">
      <Card className="bg-slate-900/90 border-slate-700 text-slate-100 backdrop-blur-md">
        <CardHeader className="py-3">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <Activity className="w-4 h-4 text-emerald-400" />
            Runtime Intelligence
          </CardTitle>
        </CardHeader>
        <CardContent className="py-2 flex flex-col gap-3">
          <div className="grid grid-cols-2 gap-2">
            <div className="bg-slate-800 p-2 rounded-lg text-center">
              <div className="text-[10px] text-slate-400 uppercase">Stability</div>
              <div className={`text-lg font-bold ${health && health.stability < 80 ? 'text-rose-400' : 'text-emerald-400'}`}>
                {health?.stability || 100}%
              </div>
            </div>
            <div className="bg-slate-800 p-2 rounded-lg text-center">
              <div className="text-[10px] text-slate-400 uppercase">Performance</div>
              <div className="text-lg font-bold text-sky-400">{Math.round(health?.performance || 0)}%</div>
            </div>
          </div>

          <div className="bg-slate-800/40 p-2 rounded-lg border border-slate-700/50">
            <div className="text-[10px] text-slate-500 uppercase mb-2 font-bold flex items-center gap-1">
              <Brain className="w-3 h-3 text-indigo-400" /> Cognitive Profile
            </div>
            <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
              <span className="text-slate-400">Style:</span>
              <span className="text-indigo-300 font-medium">Visual</span>
              <span className="text-slate-400">Speed:</span>
              <span className="text-emerald-400 font-medium">1.2x</span>
              <span className="text-slate-400">Strategy:</span>
              <span className="text-amber-400 font-medium italic">Analogical</span>
            </div>
          </div>

          <div className="space-y-1">

            <div className="text-[10px] text-slate-400 uppercase px-1">Live Telemetry</div>
            <div className="max-h-40 overflow-y-auto space-y-1 pr-1 scrollbar-hide">
              {logs.length === 0 && <div className="text-xs text-slate-500 italic p-2">Waiting for simulation...</div>}
              {logs.map((log, i) => (
                <div key={i} className="text-[10px] bg-slate-800/50 p-1.5 rounded flex justify-between items-start border border-slate-700/50">
                  <span className="flex items-center gap-1">
                    {log.type === "sim_error" && <AlertTriangle className="w-3 h-3 text-rose-400" />}
                    {log.type === "sim_interaction" && <MousePointer2 className="w-3 h-3 text-sky-400" />}
                    {log.type === "sim_performance" && <Cpu className="w-3 h-3 text-amber-400" />}
                    {log.type.replace("sim_", "")}
                  </span>
                  <span className="text-slate-500">{log.time}</span>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
