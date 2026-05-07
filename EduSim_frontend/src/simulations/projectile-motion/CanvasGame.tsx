import { useEffect, useRef, useState, useCallback, useMemo } from "react";
import {
  GRAVITIES,
  PIXELS_PER_M,
  PROJECTILE_STYLES,
  type GravityKey,
  type ProjectileType,
  type SimulationMode,
  trajectoryPoints,
  calculateRange,
  calculateMaxHeight,
  calculateTimeOfFlight,
  calculateImpactSpeed,
  getVelocityComponents,
  clampAngle,
  clampPower,
} from "./physics";

export type LiveStats = {
  power: number;
  angle: number;
  range: number;
  height: number;
  tof: number;
  impactSpeed: number;
};

export type Sample = { t: number; vx: number; vy: number; h: number };

interface Props {
  gravityKey: GravityKey;
  gravityValue?: number;
  projectileType: ProjectileType;
  mode: SimulationMode;
  manualPower?: number;
  manualAngle?: number;
  onStats: (s: LiveStats) => void;
  onSamples: (s: Sample[]) => void;
  onHit: (count: number) => void;
  launchTrigger: number;
  resetTrigger: number;
  replayTrigger: number;
  onPowerAngle: (p: number, a: number) => void;
}

interface Target {
  x: number;
  y: number;
  w: number;
  h: number;
  alive: boolean;
}

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  life: number;
  color: string;
}

interface Projectile {
  active: boolean;
  x: number;
  y: number;
  vx: number;
  vy: number;
  t: number;
  trail: { x: number; y: number }[];
}

export function CanvasGame({
  gravityKey,
  gravityValue,
  projectileType,
  mode,
  manualPower = 0,
  manualAngle = 0,
  onStats,
  onSamples,
  onHit,
  launchTrigger,
  resetTrigger,
  replayTrigger,
  onPowerAngle,
}: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState({ w: 800, h: 460 });

  // Refs for slingshot position and drag state
  const slingRef = useRef({ x: 90, y: 0 });
  const dragRef = useRef<{ active: boolean; x: number; y: number }>({
    active: false,
    x: 0,
    y: 0,
  });
  const lastLaunchTriggerRef = useRef(0);
  const isDraggingRef = useRef(false);

  // Physics state refs
  const projectileRef = useRef<Projectile | null>(null);
  const targetsRef = useRef<Target[]>([]);
  const particlesRef = useRef<Particle[]>([]);
  const samplesRef = useRef<Sample[]>([]);
  const hitsRef = useRef(0);

  // Store launch state for replay
  const stateRef = useRef<{
    launchPower: number;
    launchAngle: number;
    g: number;
  }>({
    launchPower: 0,
    launchAngle: 0,
    g: GRAVITIES[gravityKey],
  });

  const projectileStyle = PROJECTILE_STYLES[projectileType];
  const currentGravity = gravityValue ?? GRAVITIES[gravityKey];

  const resetLaunchState = useCallback(() => {
    projectileRef.current = null;
    samplesRef.current = [];
    dragRef.current = { active: false, x: 0, y: 0 };
    isDraggingRef.current = false;
    stateRef.current.launchPower = 0;
    stateRef.current.launchAngle = 0;
    onSamples([]);
    onStats({ power: 0, angle: 0, range: 0, height: 0, tof: 0, impactSpeed: 0 });
  }, [onSamples, onStats]);

  // Reset targets on size/trigger change
  const resetTargets = useCallback(() => {
    const ground = size.h - 40;
    targetsRef.current = [
      { x: size.w * 0.55, y: ground - 30, w: 30, h: 30, alive: true },
      { x: size.w * 0.65, y: ground - 60, w: 30, h: 60, alive: true },
      { x: size.w * 0.75, y: ground - 30, w: 30, h: 30, alive: true },
      { x: size.w * 0.85, y: ground - 80, w: 30, h: 80, alive: true },
    ];
    hitsRef.current = 0;
  }, [size.w, size.h]);

  // Handle canvas resize
  useEffect(() => {
    const ro = new ResizeObserver((entries) => {
      for (const e of entries) {
        const w = e.contentRect.width;
        const h = Math.max(360, Math.min(540, w * 0.55));
        setSize({ w, h });
      }
    });
    if (containerRef.current) ro.observe(containerRef.current);
    return () => ro.disconnect();
  }, []);

  // Reset state when size or trigger changes
  useEffect(() => {
    slingRef.current = { x: 90, y: size.h - 40 - 70 };
    resetTargets();
    particlesRef.current = [];
    resetLaunchState();
    onHit(0);
  }, [size.w, size.h, resetTrigger, resetTargets, resetLaunchState, onHit]);

  // Reset current projectile when switching modes so launch does not carry over.
  useEffect(() => {
    resetLaunchState();
  }, [mode, resetLaunchState]);

  // Update gravity reference
  useEffect(() => {
    stateRef.current.g = currentGravity;
  }, [currentGravity]);

  // Compute drag direction and power
  function computeDrag() {
    const sling = slingRef.current;
    const dx = sling.x - dragRef.current.x;
    const dy = sling.y - dragRef.current.y;
    const dist = Math.min(Math.hypot(dx, dy), 110);

    // Calculate angle from sling point (negate dy for canvas coordinate system)
    let angle = Math.atan2(-dy, dx) * (180 / Math.PI);
    angle = clampAngle(angle);

    // Power scales with drag distance (110 pixels = 40 m/s)
    const power = clampPower((dist / 110) * 100);

    return { power, angle };
  }

  // Launch projectile with physics
  function launchProjectile(power: number, angleDeg: number) {
    const g = currentGravity;
    const angle = clampAngle(angleDeg);
    const finalPower = clampPower(power);

    // Store launch state for replay
    stateRef.current = { launchPower: finalPower, launchAngle: angle, g };

    // Calculate velocity components
    const { vx, vy } = getVelocityComponents(finalPower, angle);

    projectileRef.current = {
      active: true,
      x: slingRef.current.x,
      y: slingRef.current.y,
      vx,
      vy,
      t: 0,
      trail: [],
    };

    samplesRef.current = [];
    resetTargets();
    onHit(0);

    // Calculate stats
    const tof = calculateTimeOfFlight(finalPower, angle, g);
    const maxH = calculateMaxHeight(finalPower, angle, g);
    const rng = calculateRange(finalPower, angle, g);

    onStats({
      power: finalPower,
      angle,
      range: rng,
      height: maxH,
      tof,
      impactSpeed: finalPower, // Will be updated on impact
    });
  }

  // Handle replay
  useEffect(() => {
    const state = stateRef.current;
    if (state.launchPower === 0 || replayTrigger === 0) return;
    launchProjectile(state.launchPower, state.launchAngle);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [replayTrigger]);

  // Handle launch trigger
  useEffect(() => {
    if (launchTrigger === lastLaunchTriggerRef.current) return;
    lastLaunchTriggerRef.current = launchTrigger;

    if (mode === "manual" && clampPower(manualPower) > 0) {
      launchProjectile(manualPower, clampAngle(manualAngle));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [launchTrigger, mode, manualPower, manualAngle, currentGravity]);

  // Main animation loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let raf = 0;
    let prev = performance.now();

    // Generate stars
    const stars = Array.from({ length: 60 }, () => ({
      x: Math.random() * size.w,
      y: Math.random() * size.h * 0.7,
      r: Math.random() * 1.4 + 0.3,
      a: Math.random() * 0.7 + 0.2,
    }));

    function tick(now: number) {
      if (!ctx) return;
      const dt = Math.min(0.033, (now - prev) / 1000);
      prev = now;
      const g = currentGravity;
      const ground = size.h - 40;

      // Clear canvas
      ctx.clearRect(0, 0, size.w, size.h);

      // Draw background gradient
      const grad = ctx.createLinearGradient(0, 0, 0, size.h);
      grad.addColorStop(0, "#0b0a1f");
      grad.addColorStop(0.6, "#15102e");
      grad.addColorStop(1, "#1a0d2e");
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, size.w, size.h);

      // Draw twinkling stars
      ctx.fillStyle = "white";
      stars.forEach((s) => {
        ctx.globalAlpha = s.a * (0.6 + 0.4 * Math.sin(now / 800 + s.x));
        ctx.beginPath();
        ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
        ctx.fill();
      });
      ctx.globalAlpha = 1;

      // Draw ground
      const groundGrad = ctx.createLinearGradient(0, ground, 0, size.h);
      groundGrad.addColorStop(0, "#3d2469");
      groundGrad.addColorStop(1, "#1a0d2e");
      ctx.fillStyle = groundGrad;
      ctx.fillRect(0, ground, size.w, size.h - ground);
      ctx.strokeStyle = "rgba(180,120,255,0.5)";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(0, ground);
      ctx.lineTo(size.w, ground);
      ctx.stroke();

      // Draw slingshot
      const sling = slingRef.current;
      ctx.strokeStyle = "#6b3e1f";
      ctx.lineWidth = 6;
      ctx.beginPath();
      ctx.moveTo(sling.x - 12, ground);
      ctx.lineTo(sling.x - 6, sling.y + 4);
      ctx.moveTo(sling.x + 12, ground);
      ctx.lineTo(sling.x + 6, sling.y + 4);
      ctx.stroke();

      // Determine projectile position
      const proj = projectileRef.current;
      let projPos = { x: sling.x, y: sling.y };

      // Handle slingshot drag preview
      if (mode === "slingshot" && dragRef.current.active && !proj?.active) {
        projPos = { x: dragRef.current.x, y: dragRef.current.y };

        // Draw drag bands
        ctx.strokeStyle = "rgba(255,200,80,0.9)";
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(sling.x - 6, sling.y + 4);
        ctx.lineTo(projPos.x, projPos.y);
        ctx.lineTo(sling.x + 6, sling.y + 4);
        ctx.stroke();

        // Draw trajectory preview
        const { power, angle } = computeDrag();
        onPowerAngle(power, angle);
        const pts = trajectoryPoints(power, angle, g, 30);
        ctx.strokeStyle = "rgba(180,120,255,0.55)";
        ctx.setLineDash([4, 6]);
        ctx.lineWidth = 2;
        ctx.beginPath();
        pts.forEach((p, i) => {
          const px = sling.x + p.x * PIXELS_PER_M;
          const py = sling.y - p.y * PIXELS_PER_M;
          if (i === 0) ctx.moveTo(px, py);
          else ctx.lineTo(px, py);
        });
        ctx.stroke();
        ctx.setLineDash([]);
      }

      // Handle manual mode trajectory preview
      if (mode === "manual" && !proj?.active && clampPower(manualPower) > 0) {
        onPowerAngle(manualPower, manualAngle);
        const pts = trajectoryPoints(manualPower, manualAngle, g, 30);
        ctx.strokeStyle = "rgba(180,120,255,0.55)";
        ctx.setLineDash([4, 6]);
        ctx.lineWidth = 2;
        ctx.beginPath();
        pts.forEach((p, i) => {
          const px = sling.x + p.x * PIXELS_PER_M;
          const py = sling.y - p.y * PIXELS_PER_M;
          if (i === 0) ctx.moveTo(px, py);
          else ctx.lineTo(px, py);
        });
        ctx.stroke();
        ctx.setLineDash([]);
      }

      // Simulate and render projectile
      if (proj && proj.active) {
        proj.t += dt;
        proj.x += proj.vx * dt * PIXELS_PER_M;
        proj.y += proj.vy * dt * PIXELS_PER_M;
        proj.vy += g * dt; // Gravity acceleration
        proj.trail.push({ x: proj.x, y: proj.y });
        if (proj.trail.length > 60) proj.trail.shift();

        // Record sample for graph
        samplesRef.current.push({
          t: proj.t,
          vx: proj.vx,
          vy: -proj.vy,
          h: Math.max(0, (sling.y - proj.y) / PIXELS_PER_M),
        });
        if (samplesRef.current.length % 3 === 0) onSamples([...samplesRef.current]);

        // Check target collisions
        for (const tg of targetsRef.current) {
          if (!tg.alive) continue;
          if (proj.x > tg.x && proj.x < tg.x + tg.w && proj.y > tg.y && proj.y < tg.y + tg.h) {
            tg.alive = false;
            hitsRef.current += 1;
            onHit(hitsRef.current);
            spawnParticles(proj.x, proj.y, "#ff6ad8");
            proj.vx *= 0.4;
            proj.vy = -Math.abs(proj.vy) * 0.5;
          }
        }

        // Check ground collision
        if (proj.y >= ground) {
          proj.y = ground;
          spawnParticles(proj.x, ground, "#a78bfa");
          const impact = calculateImpactSpeed(proj.vx, proj.vy);
          proj.active = false;
          onSamples([...samplesRef.current]);
          updateStats(impact);
        }

        // Draw projectile trail
        ctx.strokeStyle = `rgba(${hexToRgb(projectileStyle.glowColor)}, 0.9)`;
        ctx.lineWidth = 3;
        ctx.shadowColor = projectileStyle.glowColor;
        ctx.shadowBlur = 12;
        ctx.beginPath();
        proj.trail.forEach((p, i) => {
          if (i === 0) ctx.moveTo(p.x, p.y);
          else ctx.lineTo(p.x, p.y);
        });
        ctx.stroke();
        ctx.shadowBlur = 0;

        projPos = { x: proj.x, y: proj.y };
      }

      // Draw targets
      targetsRef.current.forEach((tg) => {
        if (!tg.alive) return;
        const grd = ctx.createLinearGradient(tg.x, tg.y, tg.x, tg.y + tg.h);
        grd.addColorStop(0, "#7c5fff");
        grd.addColorStop(1, "#3a2470");
        ctx.fillStyle = grd;
        ctx.shadowColor = "#7c5fff";
        ctx.shadowBlur = 14;
        roundRect(ctx, tg.x, tg.y, tg.w, tg.h, 6);
        ctx.fill();
        ctx.shadowBlur = 0;
      });

      // Update and render particles
      particlesRef.current = particlesRef.current.filter((p) => p.life > 0);
      particlesRef.current.forEach((p) => {
        p.life -= dt;
        p.x += p.vx * dt;
        p.y += p.vy * dt;
        p.vy += 200 * dt;
        ctx.globalAlpha = Math.max(0, p.life);
        ctx.fillStyle = p.color;
        ctx.beginPath();
        ctx.arc(p.x, p.y, 2.5, 0, Math.PI * 2);
        ctx.fill();
      });
      ctx.globalAlpha = 1;

      // Draw projectile with style
      ctx.save();
      ctx.shadowColor = projectileStyle.glowColor;
      ctx.shadowBlur = 16;

      if (projectileType === "square") {
        const r = projectileStyle.radius;
        ctx.fillStyle = projectileStyle.color;
        ctx.shadowBlur = 10;
        ctx.fillRect(projPos.x - r, projPos.y - r, r * 2, r * 2);
      } else {
        const bg = ctx.createRadialGradient(
          projPos.x,
          projPos.y,
          2,
          projPos.x,
          projPos.y,
          projectileStyle.radius + 4,
        );
        bg.addColorStop(0, projectileStyle.color);
        bg.addColorStop(1, darkenColor(projectileStyle.color, 0.3));
        ctx.fillStyle = bg;
        ctx.beginPath();
        ctx.arc(projPos.x, projPos.y, projectileStyle.radius, 0, Math.PI * 2);
        ctx.fill();
      }

      ctx.restore();

      // Draw projectile eyes (for bird/ball)
      if (projectileType !== "square") {
        ctx.fillStyle = "#fff";
        ctx.beginPath();
        ctx.arc(projPos.x + 3, projPos.y - 2, 2, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = "#000";
        ctx.beginPath();
        ctx.arc(projPos.x + 3, projPos.y - 2, 1, 0, Math.PI * 2);
        ctx.fill();
      }

      raf = requestAnimationFrame(tick);
    }

    function updateStats(impact: number) {
      const state = stateRef.current;
      if (state.launchPower === 0) return;
      const g = state.g;
      const a = (state.launchAngle * Math.PI) / 180;
      onStats({
        power: state.launchPower,
        angle: state.launchAngle,
        range: (state.launchPower * state.launchPower * Math.sin(2 * a)) / g,
        height: (state.launchPower * state.launchPower * Math.sin(a) ** 2) / (2 * g),
        tof: (2 * state.launchPower * Math.sin(a)) / g,
        impactSpeed: impact,
      });
    }

    function spawnParticles(x: number, y: number, color: string) {
      for (let i = 0; i < 24; i++) {
        const ang = Math.random() * Math.PI * 2;
        const sp = Math.random() * 180 + 40;
        particlesRef.current.push({
          x,
          y,
          vx: Math.cos(ang) * sp,
          vy: Math.sin(ang) * sp - 60,
          life: 0.8,
          color,
        });
      }
    }

    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [
    size.w,
    size.h,
    gravityKey,
    projectileType,
    mode,
    manualPower,
    manualAngle,
    onStats,
    onSamples,
    onHit,
    onPowerAngle,
  ]);

  // Get mouse position relative to canvas
  function getMouse(e: React.PointerEvent) {
    const rect = canvasRef.current!.getBoundingClientRect();
    return { x: e.clientX - rect.left, y: e.clientY - rect.top };
  }

  return (
    <div ref={containerRef} className="w-full">
      <canvas
        ref={canvasRef}
        width={size.w}
        height={size.h}
        className="w-full rounded-3xl cursor-grab active:cursor-grabbing"
        style={{ height: size.h }}
        onPointerDown={(e) => {
          if (mode !== "slingshot") return;
          (e.target as Element).setPointerCapture(e.pointerId);
          const m = getMouse(e);
          if (Math.hypot(m.x - slingRef.current.x, m.y - slingRef.current.y) < 80) {
            isDraggingRef.current = true;
            dragRef.current = { active: true, x: m.x, y: m.y };
          }
        }}
        onPointerMove={(e) => {
          if (mode !== "slingshot" || !isDraggingRef.current) return;
          const m = getMouse(e);
          const sling = slingRef.current;

          // Circular drag constraint
          const dx = m.x - sling.x;
          const dy = m.y - sling.y;
          const dist = Math.hypot(dx, dy);
          const maxDist = 110;

          if (dist > maxDist) {
            const ratio = maxDist / dist;
            dragRef.current.x = sling.x + dx * ratio;
            dragRef.current.y = sling.y + dy * ratio;
          } else {
            dragRef.current.x = m.x;
            dragRef.current.y = m.y;
          }
        }}
        onPointerUp={() => {
          if (mode !== "slingshot" || !isDraggingRef.current) {
            dragRef.current.active = false;
            isDraggingRef.current = false;
            return;
          }

          const { power, angle } = computeDrag();
          dragRef.current.active = false;
          isDraggingRef.current = false;

          if (power > 0) {
            launchProjectile(power, angle);
          }
        }}
      />
    </div>
  );
}

// Utility functions
function roundRect(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  w: number,
  h: number,
  r: number,
) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.arcTo(x + w, y, x + w, y + h, r);
  ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r);
  ctx.arcTo(x, y, x + w, y, r);
  ctx.closePath();
}

function hexToRgb(hex: string): string {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  if (!result) return "168, 139, 250";
  const r = parseInt(result[1], 16);
  const g = parseInt(result[2], 16);
  const b = parseInt(result[3], 16);
  return `${r}, ${g}, ${b}`;
}

function darkenColor(hex: string, amount: number): string {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  if (!result) return hex;
  let r = parseInt(result[1], 16);
  let g = parseInt(result[2], 16);
  let b = parseInt(result[3], 16);
  r = Math.max(0, Math.floor(r * (1 - amount)));
  g = Math.max(0, Math.floor(g * (1 - amount)));
  b = Math.max(0, Math.floor(b * (1 - amount)));
  return `#${r.toString(16).padStart(2, "0")}${g.toString(16).padStart(2, "0")}${b.toString(16).padStart(2, "0")}`;
}
