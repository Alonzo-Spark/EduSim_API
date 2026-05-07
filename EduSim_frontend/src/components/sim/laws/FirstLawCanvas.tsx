import { useEffect, useRef } from "react";
import type { LawSample } from "./types";

type Props = {
  mass: number;
  friction: number;
  velocity: number;
  showVectors: boolean;
  running: boolean;
  brakeTrigger: number;
  resetTrigger: number;
  onSamples: (s: LawSample[]) => void;
  onLive: (d: { busV: number; objV: number; netF: number; inertia: number }) => void;
};

export function FirstLawCanvas({
  mass, friction, velocity, showVectors, running, brakeTrigger, resetTrigger, onSamples, onLive,
}: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const stateRef = useRef({
    busX: 100, busV: 0, objX: 160, objV: 0,
    time: 0, braking: false, samples: [] as LawSample[],
  });
  const propsRef = useRef({ mass, friction, velocity, showVectors, running });
  propsRef.current = { mass, friction, velocity, showVectors, running };

  // Reset
  useEffect(() => {
    const s = stateRef.current;
    s.busX = 100; s.busV = 0; s.objX = 160; s.objV = 0;
    s.time = 0; s.braking = false; s.samples = [];
    onSamples([]);
  }, [resetTrigger, onSamples]);

  // Brake
  useEffect(() => {
    if (brakeTrigger > 0) stateRef.current.braking = true;
  }, [brakeTrigger]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d")!;
    let raf = 0;
    let prev = performance.now();

    const tick = (now: number) => {
      const rawDt = (now - prev) / 1000;
      prev = now;
      const p = propsRef.current;
      const s = stateRef.current;
      const dt = p.running ? Math.min(rawDt, 0.033) : 0;

      if (dt > 0) {
        s.time += dt;
        const targetBusV = s.braking ? 0 : p.velocity;
        s.busV += (targetBusV - s.busV) * (s.braking ? 3 : 2) * dt;
        s.busX += s.busV * 30 * dt;

        const frictionForce = p.friction * p.mass * 9.8;
        const netF = -Math.sign(s.objV) * frictionForce;
        if (!s.braking) {
          s.objV = s.busV;
        } else {
          s.objV += (netF / p.mass) * dt;
          if (Math.abs(s.objV) < 0.05) s.objV = 0;
        }
        s.objX += s.objV * 30 * dt;

        // Clamp positions for wrap-around
        const W = canvas.clientWidth;
        if (s.busX > W + 100) { s.busX = -100; s.objX = s.busX + 60; }

        s.samples.push({ t: +s.time.toFixed(2), v: +s.objV.toFixed(2), a: +(netF / p.mass).toFixed(2), x: +s.objX.toFixed(1), f: +netF.toFixed(2) });
        if (s.samples.length > 300) s.samples.shift();
        if (Math.floor(s.time * 15) !== Math.floor((s.time - dt) * 15)) {
          onSamples([...s.samples]);
          onLive({ busV: s.busV, objV: s.objV, netF: s.braking ? netF : 0, inertia: p.mass * s.objV });
        }
      }

      // ── Render ─────────────────────────────────────
      const dpr = window.devicePixelRatio || 1;
      const W = canvas.clientWidth, H = canvas.clientHeight;
      canvas.width = W * dpr; canvas.height = H * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

      // Background
      const bg = ctx.createLinearGradient(0, 0, W, H);
      bg.addColorStop(0, "#020617"); bg.addColorStop(0.5, "#0f172a"); bg.addColorStop(1, "#111827");
      ctx.fillStyle = bg; ctx.fillRect(0, 0, W, H);

      // Grid
      ctx.strokeStyle = "rgba(148,163,184,0.06)"; ctx.lineWidth = 1;
      for (let x = 0; x < W; x += 40) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke(); }
      for (let y = 0; y < H; y += 40) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }

      // Road
      const roadY = H * 0.72;
      ctx.fillStyle = "rgba(255,255,255,0.04)"; ctx.fillRect(0, roadY, W, H - roadY);
      ctx.fillStyle = "rgba(148,163,184,0.2)"; ctx.fillRect(0, roadY - 2, W, 4);

      // Bus
      const bx = s.busX % (W + 200) - 100;
      ctx.save();
      ctx.shadowColor = "#a78bfa"; ctx.shadowBlur = 20;
      ctx.fillStyle = "#6d28d9"; roundRect(ctx, bx, roadY - 50, 120, 48, 8); ctx.fill();
      ctx.shadowBlur = 0;
      ctx.fillStyle = "rgba(255,255,255,0.15)"; roundRect(ctx, bx + 8, roadY - 44, 30, 20, 4); ctx.fill();
      roundRect(ctx, bx + 44, roadY - 44, 30, 20, 4); ctx.fill();
      // Wheels
      ctx.fillStyle = "#1e1b4b";
      ctx.beginPath(); ctx.arc(bx + 25, roadY, 8, 0, Math.PI * 2); ctx.fill();
      ctx.beginPath(); ctx.arc(bx + 95, roadY, 8, 0, Math.PI * 2); ctx.fill();
      ctx.restore();

      // Object on bus
      const ox = s.objX % (W + 200) - 100;
      ctx.save();
      ctx.shadowColor = "#7dd3fc"; ctx.shadowBlur = 18;
      ctx.fillStyle = "#0ea5e9";
      ctx.beginPath(); ctx.arc(ox, roadY - 66, 14, 0, Math.PI * 2); ctx.fill();
      ctx.shadowBlur = 0;
      ctx.strokeStyle = "rgba(255,255,255,0.3)"; ctx.lineWidth = 2; ctx.stroke();
      ctx.fillStyle = "white"; ctx.font = "bold 10px system-ui"; ctx.textAlign = "center";
      ctx.fillText(`${p.mass}kg`, ox, roadY - 63);
      ctx.restore();

      // Vectors
      if (p.showVectors && s.braking) {
        const vLen = Math.min(80, Math.abs(s.objV) * 8);
        if (vLen > 2) {
          drawArrow(ctx, ox, roadY - 66, ox + vLen * Math.sign(s.objV), roadY - 66, "#7dd3fc", "v");
        }
        const fLen = Math.min(60, Math.abs(-p.friction * p.mass * 9.8) * 2);
        if (fLen > 2 && s.objV !== 0) {
          drawArrow(ctx, ox, roadY - 40, ox - fLen * Math.sign(s.objV), roadY - 40, "#f472b6", "friction");
        }
      }

      // Label
      ctx.fillStyle = "rgba(255,255,255,0.5)"; ctx.font = "11px system-ui"; ctx.textAlign = "left";
      ctx.fillText(s.braking ? "Braking — inertia keeps object moving" : "Moving together", 16, 24);

      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [onSamples, onLive]);

  return <canvas ref={canvasRef} className="w-full h-full rounded-2xl" style={{ minHeight: 340 }} />;
}

function roundRect(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, r: number) {
  ctx.beginPath();
  ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r); ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r); ctx.closePath();
}

function drawArrow(ctx: CanvasRenderingContext2D, x1: number, y1: number, x2: number, y2: number, color: string, label: string) {
  const angle = Math.atan2(y2 - y1, x2 - x1);
  ctx.save();
  ctx.strokeStyle = color; ctx.fillStyle = color; ctx.shadowColor = color; ctx.shadowBlur = 10;
  ctx.lineWidth = 3; ctx.lineCap = "round";
  ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
  ctx.beginPath();
  ctx.moveTo(x2, y2);
  ctx.lineTo(x2 - Math.cos(angle - 0.4) * 10, y2 - Math.sin(angle - 0.4) * 10);
  ctx.lineTo(x2 - Math.cos(angle + 0.4) * 10, y2 - Math.sin(angle + 0.4) * 10);
  ctx.closePath(); ctx.fill();
  ctx.shadowBlur = 0; ctx.font = "10px system-ui"; ctx.fillText(label, (x1 + x2) / 2, y1 - 8);
  ctx.restore();
}
