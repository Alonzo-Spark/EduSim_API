import { type Sample } from "./CanvasGame";

export function GraphPanel({ samples, T }: { samples: Sample[]; T: number }) {
  const graphs = [
    {
      title: "Horizontal Velocity",
      subtitle: "vx vs time",
      color: "var(--neon-cyan)",
      unit: "m/s",
      get: (s: Sample) => s.vx,
      yLabel: "Velocity (m/s)",
      xLabel: "Time (s)",
    },
    {
      title: "Vertical Velocity",
      subtitle: "vy vs time",
      color: "var(--neon-purple)",
      unit: "m/s",
      get: (s: Sample) => s.vy,
      yLabel: "Velocity (m/s)",
      xLabel: "Time (s)",
    },
    {
      title: "Height",
      subtitle: "h vs time",
      color: "var(--neon-blue)",
      unit: "m",
      get: (s: Sample) => s.h,
      yLabel: "Height (m)",
      xLabel: "Time (s)",
    },
  ];

  return (
    <div className="glass-strong rounded-3xl p-4 grid grid-cols-1 lg:grid-cols-3 gap-3">
      {graphs.map((graph) => (
        <Graph
          key={graph.title}
          title={graph.title}
          subtitle={graph.subtitle}
          color={graph.color}
          unit={graph.unit}
          samples={samples}
          get={graph.get}
          T={Math.max(T, samples[samples.length - 1]?.t ?? 0.01, 0.01)}
          xLabel={graph.xLabel}
          yLabel={graph.yLabel}
        />
      ))}
    </div>
  );
}

function Graph({
  title,
  subtitle,
  color,
  unit,
  samples,
  get,
  T,
  xLabel,
  yLabel,
}: {
  title: string;
  subtitle: string;
  color: string;
  unit: string;
  samples: Sample[];
  get: (s: Sample) => number;
  T: number;
  xLabel: string;
  yLabel: string;
}) {
  const W = 320;
  const H = 220;
  const PAD = { left: 54, right: 18, top: 22, bottom: 42 };
  const plotW = W - PAD.left - PAD.right;
  const plotH = H - PAD.top - PAD.bottom;

  const values = samples.map(get);
  const maxAbs = Math.max(1, ...values.map((v) => Math.abs(v)));
  const minValue = samples.length ? Math.min(...values) : 0;
  const maxValue = samples.length ? Math.max(...values) : 1;

  const yDomain = buildDomain(title === "Height" ? 0 : minValue, maxValue, maxAbs);
  const xDomain = { min: 0, max: T };

  const path = samples
    .map((sample, index) => {
      const x = scale(sample.t, xDomain.min, xDomain.max, PAD.left, PAD.left + plotW);
      const y = scale(get(sample), yDomain.min, yDomain.max, PAD.top + plotH, PAD.top);
      return `${index === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");

  const xTicks = makeTicks(xDomain.min, xDomain.max, 4);
  const yTicks = makeTicks(yDomain.min, yDomain.max, 4);
  const last = samples[samples.length - 1];
  const lastValue = last ? get(last) : null;

  return (
    <div className="glass rounded-2xl p-3 space-y-2">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="text-sm font-semibold text-foreground">{title}</div>
          <div className="text-[11px] uppercase tracking-[0.22em] text-muted-foreground">
            {subtitle}
          </div>
        </div>
        <div className="text-right">
          <div className="font-mono text-xs" style={{ color }}>
            {lastValue !== null ? `${lastValue.toFixed(1)} ${unit}` : "—"}
          </div>
          <div className="text-[10px] text-muted-foreground">Current value</div>
        </div>
      </div>

      <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-[220px] overflow-visible">
        {/* Plot background */}
        <rect
          x={PAD.left}
          y={PAD.top}
          width={plotW}
          height={plotH}
          rx="12"
          fill="rgba(255,255,255,0.03)"
          stroke="rgba(255,255,255,0.08)"
        />

        {/* Grid + ticks */}
        {xTicks.map((tick) => {
          const x = scale(tick, xDomain.min, xDomain.max, PAD.left, PAD.left + plotW);
          return (
            <g key={`x-${tick}`}>
              <line
                x1={x}
                y1={PAD.top}
                x2={x}
                y2={PAD.top + plotH}
                stroke="rgba(255,255,255,0.12)"
                strokeDasharray="3 5"
              />
              <text
                x={x}
                y={H - 14}
                textAnchor="middle"
                className="fill-muted-foreground"
                fontSize="10"
              >
                {tick.toFixed(1)}
              </text>
            </g>
          );
        })}

        {yTicks.map((tick) => {
          const y = scale(tick, yDomain.min, yDomain.max, PAD.top + plotH, PAD.top);
          return (
            <g key={`y-${tick}`}>
              <line
                x1={PAD.left}
                y1={y}
                x2={PAD.left + plotW}
                y2={y}
                stroke="rgba(255,255,255,0.12)"
                strokeDasharray="3 5"
              />
              <text
                x={PAD.left - 10}
                y={y + 3}
                textAnchor="end"
                className="fill-muted-foreground"
                fontSize="10"
              >
                {tick.toFixed(1)}
              </text>
            </g>
          );
        })}

        {/* Axes */}
        <line
          x1={PAD.left}
          y1={PAD.top + plotH}
          x2={PAD.left + plotW}
          y2={PAD.top + plotH}
          stroke="rgba(255,255,255,0.35)"
        />
        <line
          x1={PAD.left}
          y1={PAD.top}
          x2={PAD.left}
          y2={PAD.top + plotH}
          stroke="rgba(255,255,255,0.35)"
        />

        {/* Zero line */}
        {yDomain.min < 0 && yDomain.max > 0 && (
          <line
            x1={PAD.left}
            y1={scale(0, yDomain.min, yDomain.max, PAD.top + plotH, PAD.top)}
            x2={PAD.left + plotW}
            y2={scale(0, yDomain.min, yDomain.max, PAD.top + plotH, PAD.top)}
            stroke="rgba(255,255,255,0.35)"
            strokeDasharray="4 4"
          />
        )}

        {/* Data path */}
        {path && (
          <path
            d={path}
            fill="none"
            stroke={color}
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            style={{ filter: `drop-shadow(0 0 5px ${color})` }}
          />
        )}

        {/* Last point marker */}
        {last && (
          <circle
            cx={scale(last.t, xDomain.min, xDomain.max, PAD.left, PAD.left + plotW)}
            cy={scale(get(last), yDomain.min, yDomain.max, PAD.top + plotH, PAD.top)}
            r="3.5"
            fill={color}
          />
        )}

        {/* Axis labels */}
        <text
          x={PAD.left + plotW / 2}
          y={H - 4}
          textAnchor="middle"
          className="fill-muted-foreground"
          fontSize="11"
        >
          {xLabel}
        </text>
        <text
          x={14}
          y={PAD.top + plotH / 2}
          textAnchor="middle"
          className="fill-muted-foreground"
          fontSize="11"
          transform={`rotate(-90 14 ${PAD.top + plotH / 2})`}
        >
          {yLabel}
        </text>
      </svg>
    </div>
  );
}

function scale(value: number, inMin: number, inMax: number, outMin: number, outMax: number) {
  if (Math.abs(inMax - inMin) < 1e-6) return (outMin + outMax) / 2;
  const ratio = (value - inMin) / (inMax - inMin);
  return outMin + ratio * (outMax - outMin);
}

function buildDomain(minValue: number, maxValue: number, maxAbs: number) {
  const lower = Math.min(minValue, 0);
  const upper = Math.max(maxValue, 0);
  const span = Math.max(upper - lower, maxAbs * 0.25, 1);
  const pad = span * 0.18;
  if (lower === upper) {
    return { min: lower - pad, max: upper + pad };
  }
  return { min: lower - pad, max: upper + pad };
}

function makeTicks(min: number, max: number, count: number) {
  const ticks: number[] = [];
  if (count <= 1) return [min, max];
  const step = (max - min) / (count - 1);
  for (let i = 0; i < count; i++) {
    ticks.push(min + step * i);
  }
  return ticks;
}
