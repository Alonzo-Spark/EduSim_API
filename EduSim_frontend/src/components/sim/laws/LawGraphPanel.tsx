import type { LawSample } from "./types";

type SeriesDef = {
  title: string;
  color: string;
  unit: string;
  get: (s: LawSample) => number;
};

export function LawGraphPanel({ samples, series }: { samples: LawSample[]; series: SeriesDef[] }) {
  return (
    <div className="glass-strong rounded-3xl p-4 grid grid-cols-1 md:grid-cols-3 gap-3">
      {series.map((s) => (
        <Graph key={s.title} title={s.title} color={s.color} unit={s.unit} samples={samples} get={s.get} />
      ))}
    </div>
  );
}

function Graph({ title, color, unit, samples, get }: {
  title: string; color: string; unit: string; samples: LawSample[]; get: (s: LawSample) => number;
}) {
  const W = 280, H = 100, PAD = 8;
  const ys = samples.map(get);
  const maxT = samples.length > 0 ? samples[samples.length - 1].t : 1;
  const minY = Math.min(0, ...ys);
  const maxY = Math.max(1, ...ys.map(Math.abs), ...ys);
  const span = maxY - minY || 1;

  const path = samples
    .map((s, i) => {
      const x = PAD + (s.t / Math.max(maxT, 0.01)) * (W - PAD * 2);
      const y = H - PAD - ((get(s) - minY) / span) * (H - PAD * 2);
      return `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");

  const last = samples[samples.length - 1];

  return (
    <div className="glass rounded-2xl p-3">
      <div className="flex items-baseline justify-between mb-1">
        <div className="text-xs font-semibold">{title}</div>
        <div className="font-mono text-xs" style={{ color }}>
          {last ? `${get(last).toFixed(1)} ${unit}` : "—"}
        </div>
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-[100px]">
        {/* Grid */}
        {[1, 2, 3].map((i) => (
          <line key={`h${i}`} x1={PAD} y1={(H / 4) * i} x2={W - PAD} y2={(H / 4) * i} stroke="white" strokeOpacity="0.06" />
        ))}
        <line x1={PAD} y1={H - PAD} x2={W - PAD} y2={H - PAD} stroke="white" strokeOpacity="0.12" />
        <line x1={PAD} y1={PAD} x2={PAD} y2={H - PAD} stroke="white" strokeOpacity="0.12" />
        {path && (
          <path d={path} fill="none" stroke={color} strokeWidth="2" strokeLinejoin="round"
            style={{ filter: `drop-shadow(0 0 6px ${color})` }} />
        )}
      </svg>
    </div>
  );
}
