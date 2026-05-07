import { useEffect, useRef } from "react";
import type { LawSample } from "./types";

type Props = {
  force: number;
  mass: number;
  showVectors: boolean;
  running: boolean;
  resetTrigger: number;
  onSamples: (s: LawSample[]) => void;
  onLive: (d: { force: number; mass: number; accel: number; velocity: number; displacement: number }) => void;
};

export function SecondLawCanvas({ force, mass, showVectors, running, resetTrigger, onSamples, onLive }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const stateRef = useRef({ x: 120, v: 0, time: 0, samples: [] as LawSample[] });
  const propsRef = useRef({ force, mass, showVectors, running });
  propsRef.current = { force, mass, showVectors, running };

  useEffect(() => {
    const s = stateRef.current;
    s.x = 120; s.v = 0; s.time = 0; s.samples = [];
    onSamples([]);
  }, [resetTrigger, onSamples]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d")!;
    let raf = 0, prev = performance.now();

    const tick = (now: number) => {
      const rawDt = (now - prev) / 1000; prev = now;
      const p = propsRef.current;
      const s = stateRef.current;
      const dt = p.running ? Math.min(rawDt, 0.033) : 0;

      if (dt > 0) {
        s.time += dt;
        const a = p.force / Math.max(0.1, p.mass);
        s.v += a * dt;
        s.x += s.v * 20 * dt;

        const W = canvas.clientWidth;
        if (s.x > W + 50) { s.x = 80; s.v *= 0.3; }

        s.samples.push({ t: +s.time.toFixed(2), v: +s.v.toFixed(2), a: +a.toFixed(2), x: +s.x.toFixed(1), f: +p.force.toFixed(1) });
        if (s.samples.length > 300) s.samples.shift();
        if (Math.floor(s.time * 15) !== Math.floor((s.time - dt) * 15)) {
          onSamples([...s.samples]);
          onLive({ force: p.force, mass: p.mass, accel: a, velocity: s.v, displacement: s.x - 120 });
        }
      }

      const dpr = window.devicePixelRatio || 1;
      const W = canvas.clientWidth, H = canvas.clientHeight;
      canvas.width = W * dpr; canvas.height = H * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

      const bg = ctx.createLinearGradient(0, 0, W, H);
      bg.addColorStop(0, "#020617"); bg.addColorStop(0.5, "#0f172a"); bg.addColorStop(1, "#111827");
      ctx.fillStyle = bg; ctx.fillRect(0, 0, W, H);

      ctx.strokeStyle = "rgba(148,163,184,0.06)"; ctx.lineWidth = 1;
      for (let x = 0; x < W; x += 40) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke(); }
      for (let y = 0; y < H; y += 40) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }

      const trackY = H * 0.65;
      ctx.fillStyle = "rgba(255,255,255,0.03)"; ctx.fillRect(0, trackY, W, 6);
      ctx.fillStyle = "rgba(148,163,184,0.15)"; ctx.fillRect(0, trackY, W, 2);

      // Cart
      const cx = s.x;
      const cartW = 60 + p.mass * 3;
      const cartH = 36 + p.mass * 1.5;
      ctx.save();
      ctx.shadowColor = "#a78bfa"; ctx.shadowBlur = 18;
      ctx.fillStyle = "#7c3aed";
      roundRect(ctx, cx - cartW / 2, trackY - cartH, cartW, cartH, 6); ctx.fill();
      ctx.shadowBlur = 0;
      ctx.fillStyle = "rgba(255,255,255,0.12)";
      roundRect(ctx, cx - cartW / 2 + 4, trackY - cartH + 4, cartW - 8, cartH / 2, 3); ctx.fill();
      ctx.fillStyle = "#1e1b4b";
      ctx.beginPath(); ctx.arc(cx - cartW / 3, trackY + 2, 6, 0, Math.PI * 2); ctx.fill();
      ctx.beginPath(); ctx.arc(cx + cartW / 3, trackY + 2, 6, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = "white"; ctx.font = "bold 10px system-ui"; ctx.textAlign = "center";
      ctx.fillText(`${p.mass.toFixed(0)}kg`, cx, trackY - cartH / 2 + 4);
      ctx.restore();

      if (p.showVectors) {
        const fLen = Math.min(100, p.force * 4);
        if (fLen > 2) drawArrow(ctx, cx + cartW / 2 + 4, trackY - cartH / 2, cx + cartW / 2 + 4 + fLen, trackY - cartH / 2, "#ff6ad8", `F=${p.force.toFixed(0)}N`);
        const aLen = Math.min(80, (p.force / Math.max(0.1, p.mass)) * 10);
        if (aLen > 2) drawArrow(ctx, cx, trackY - cartH - 12, cx + aLen, trackY - cartH - 12, "#7dd3fc", `a=${(p.force / Math.max(0.1, p.mass)).toFixed(1)}`);
        const vLen = Math.min(80, Math.abs(s.v) * 6);
        if (vLen > 2) drawArrow(ctx, cx, trackY + 16, cx + vLen, trackY + 16, "#fda4af", `v=${s.v.toFixed(1)}`);
      }

      ctx.fillStyle = "rgba(255,255,255,0.5)"; ctx.font = "11px system-ui"; ctx.textAlign = "left";
      ctx.fillText(`F = ${p.force.toFixed(0)} N  ·  m = ${p.mass.toFixed(0)} kg  ·  a = ${(p.force / Math.max(0.1, p.mass)).toFixed(2)} m/s²`, 16, 24);

      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [onSamples, onLive]);

  return <canvas ref={canvasRef} className="w-full h-full rounded-2xl" style={{ minHeight: 340 }} />;
}

function roundRect(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, r: number) {
  ctx.beginPath(); ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r); ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r); ctx.closePath();
}

function drawArrow(ctx: CanvasRenderingContext2D, x1: number, y1: number, x2: number, y2: number, color: string, label: string) {
  const angle = Math.atan2(y2 - y1, x2 - x1);
  ctx.save(); ctx.strokeStyle = color; ctx.fillStyle = color; ctx.shadowColor = color; ctx.shadowBlur = 10;
  ctx.lineWidth = 3; ctx.lineCap = "round";
  ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(x2, y2);
  ctx.lineTo(x2 - Math.cos(angle - 0.4) * 10, y2 - Math.sin(angle - 0.4) * 10);
  ctx.lineTo(x2 - Math.cos(angle + 0.4) * 10, y2 - Math.sin(angle + 0.4) * 10);
  ctx.closePath(); ctx.fill();
  ctx.shadowBlur = 0; ctx.font = "10px system-ui"; ctx.fillText(label, (x1 + x2) / 2, y1 - 8);
  ctx.restore();
}
