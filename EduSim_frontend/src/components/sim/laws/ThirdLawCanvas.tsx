import { useEffect, useRef } from "react";
import type { LawSample } from "./types";

type Props = {
  thrust: number;
  massA: number;
  massB: number;
  showVectors: boolean;
  running: boolean;
  launchTrigger: number;
  resetTrigger: number;
  onSamples: (s: LawSample[]) => void;
  onLive: (d: { thrust: number; reaction: number; momentum: number; vA: number; vB: number }) => void;
};

type Particle = { x: number; y: number; vx: number; vy: number; life: number };

export function ThirdLawCanvas({ thrust, massA, massB, showVectors, running, launchTrigger, resetTrigger, onSamples, onLive }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const stateRef = useRef({
    aX: 0, bX: 0, aV: 0, bV: 0, time: 0,
    active: false, particles: [] as Particle[], samples: [] as LawSample[],
  });
  const propsRef = useRef({ thrust, massA, massB, showVectors, running });
  propsRef.current = { thrust, massA, massB, showVectors, running };

  useEffect(() => {
    const s = stateRef.current;
    s.aX = 0; s.bX = 0; s.aV = 0; s.bV = 0;
    s.time = 0; s.active = false; s.particles = []; s.samples = [];
    onSamples([]);
  }, [resetTrigger, onSamples]);

  useEffect(() => {
    if (launchTrigger > 0) stateRef.current.active = true;
  }, [launchTrigger]);

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
        if (s.active) {
          const aA = p.thrust / Math.max(0.1, p.massA);
          const aB = p.thrust / Math.max(0.1, p.massB);
          
          // Only apply continuous thrust for the first 1.5 seconds, 
          // like an actual explosion or launch, rather than infinite force.
          if (s.time < 1.5) {
            s.aV -= aA * dt; // A goes left (reaction)
            s.bV += aB * dt; // B goes right (action on B)
          }

          s.aX += s.aV * 20 * dt;
          s.bX += s.bV * 20 * dt;

          const limit = canvas.clientWidth / 2 - 50; 
          
          // Bounce off left wall
          if (s.aX - 30 < -limit) {
            s.aX = -limit + 30;
            s.aV *= -0.7; // lose some energy on bounce
          }
          // Bounce off right wall
          if (s.bX + 30 > limit) {
            s.bX = limit - 30;
            s.bV *= -0.7;
          }

          // Exhaust particles (only while thrusting)
          if (Math.random() < 0.6 && s.time < 1.5) {
            const cx = canvas.clientWidth / 2;
            s.particles.push({
              x: cx + s.aX + 20, y: canvas.clientHeight / 2 + (Math.random() - 0.5) * 12,
              vx: -80 - Math.random() * 60, vy: (Math.random() - 0.5) * 40,
              life: 1,
            });
          }
        }

        // Update particles
        for (const pt of s.particles) {
          pt.x += pt.vx * dt; pt.y += pt.vy * dt; pt.life -= dt * 2;
        }
        s.particles = s.particles.filter((pt) => pt.life > 0);

        s.samples.push({ t: +s.time.toFixed(2), v: +s.bV.toFixed(2), a: +(p.thrust / Math.max(0.1, p.massB)).toFixed(2), x: +s.bX.toFixed(1), f: +p.thrust.toFixed(1) });
        if (s.samples.length > 300) s.samples.shift();
        if (Math.floor(s.time * 15) !== Math.floor((s.time - dt) * 15)) {
          onSamples([...s.samples]);
          onLive({ thrust: p.thrust, reaction: p.thrust, momentum: p.massA * Math.abs(s.aV) + p.massB * Math.abs(s.bV), vA: s.aV, vB: s.bV });
        }
      }

      const dpr = window.devicePixelRatio || 1;
      const W = canvas.clientWidth, H = canvas.clientHeight;
      canvas.width = W * dpr; canvas.height = H * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

      const bg = ctx.createLinearGradient(0, 0, W, H);
      bg.addColorStop(0, "#020617"); bg.addColorStop(0.5, "#0a0e27"); bg.addColorStop(1, "#111827");
      ctx.fillStyle = bg; ctx.fillRect(0, 0, W, H);

      // Stars
      ctx.fillStyle = "rgba(255,255,255,0.3)";
      for (let i = 0; i < 40; i++) {
        const sx = ((i * 137.5) % W), sy = ((i * 97.3) % H);
        ctx.fillRect(sx, sy, 1.5, 1.5);
      }

      ctx.strokeStyle = "rgba(148,163,184,0.04)"; ctx.lineWidth = 1;
      for (let x = 0; x < W; x += 40) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke(); }

      const cx = W / 2, cy = H / 2;

      // Draw walls
      ctx.fillStyle = "rgba(148,163,184,0.15)";
      ctx.fillRect(50, cy - 80, 10, 160); // Left wall
      ctx.fillRect(W - 60, cy - 80, 10, 160); // Right wall
      
      // Wall glow
      ctx.shadowColor = "#94a3b8"; ctx.shadowBlur = 10;
      ctx.fillStyle = "rgba(148,163,184,0.5)";
      ctx.fillRect(50, cy - 80, 2, 160);
      ctx.fillRect(W - 52, cy - 80, 2, 160);
      ctx.shadowBlur = 0;

      // Exhaust particles
      for (const pt of s.particles) {
        ctx.save();
        ctx.globalAlpha = pt.life * 0.6;
        ctx.shadowColor = "#ff6ad8"; ctx.shadowBlur = 8;
        ctx.fillStyle = `hsl(${320 + pt.life * 30}, 80%, ${50 + pt.life * 30}%)`;
        ctx.beginPath(); ctx.arc(pt.x, pt.y, 2 + pt.life * 2, 0, Math.PI * 2); ctx.fill();
        ctx.restore();
      }

      // Object A (left, larger = heavier)
      const aR = 18 + p.massA * 1.5;
      ctx.save();
      ctx.shadowColor = "#f0abfc"; ctx.shadowBlur = 20;
      ctx.fillStyle = "#a855f7";
      ctx.beginPath(); ctx.arc(cx + s.aX - 30, cy, aR, 0, Math.PI * 2); ctx.fill();
      ctx.shadowBlur = 0; ctx.strokeStyle = "rgba(255,255,255,0.25)"; ctx.lineWidth = 2; ctx.stroke();
      ctx.fillStyle = "white"; ctx.font = "bold 10px system-ui"; ctx.textAlign = "center";
      ctx.fillText(`A: ${p.massA}kg`, cx + s.aX - 30, cy + 4);
      ctx.restore();

      // Object B (right)
      const bR = 18 + p.massB * 1.5;
      ctx.save();
      ctx.shadowColor = "#7dd3fc"; ctx.shadowBlur = 20;
      ctx.fillStyle = "#0ea5e9";
      ctx.beginPath(); ctx.arc(cx + s.bX + 30, cy, bR, 0, Math.PI * 2); ctx.fill();
      ctx.shadowBlur = 0; ctx.strokeStyle = "rgba(255,255,255,0.25)"; ctx.lineWidth = 2; ctx.stroke();
      ctx.fillStyle = "white"; ctx.font = "bold 10px system-ui"; ctx.textAlign = "center";
      ctx.fillText(`B: ${p.massB}kg`, cx + s.bX + 30, cy + 4);
      ctx.restore();

      // Vectors
      if (p.showVectors && s.active) {
        const fLen = Math.min(80, p.thrust * 3);
        drawArrow(ctx, cx + s.aX - 30 - aR, cy, cx + s.aX - 30 - aR - fLen, cy, "#f0abfc", "Reaction");
        drawArrow(ctx, cx + s.bX + 30 + bR, cy, cx + s.bX + 30 + bR + fLen, cy, "#7dd3fc", "Action");
      }

      ctx.fillStyle = "rgba(255,255,255,0.5)"; ctx.font = "11px system-ui"; ctx.textAlign = "left";
      ctx.fillText(s.active ? `F_AB = ${p.thrust.toFixed(0)} N  ·  F_BA = −${p.thrust.toFixed(0)} N` : "Press Launch to trigger action–reaction", 16, 24);

      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [onSamples, onLive]);

  return <canvas ref={canvasRef} className="w-full h-full rounded-2xl" style={{ minHeight: 340 }} />;
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
  ctx.shadowBlur = 0; ctx.font = "10px system-ui"; ctx.fillText(label, (x1 + x2) / 2, y1 - 10);
  ctx.restore();
}
