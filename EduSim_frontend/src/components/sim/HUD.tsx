type Stat = { label: string; value: string; unit: string; color: string };

export function HUD({ stats }: { stats: Stat[] }) {
  return (
    <div className="glass-strong rounded-3xl p-4 grid grid-cols-2 md:grid-cols-4 gap-3">
      {stats.map((s) => (
        <div key={s.label} className="glass rounded-2xl p-3">
          <div className="text-[10px] uppercase tracking-widest text-muted-foreground">
            {s.label}
          </div>
          <div className="flex items-baseline gap-1 mt-1">
            <span
              className="text-2xl font-bold font-mono"
              style={{ color: s.color, textShadow: `0 0 12px ${s.color}` }}
            >
              {s.value}
            </span>
            <span className="text-xs text-muted-foreground">{s.unit}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
