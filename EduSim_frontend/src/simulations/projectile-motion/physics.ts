// Physics constants and types for projectile motion simulation

export type GravityKey = "Earth" | "Moon" | "Mars";
export type ProjectileType = "ball" | "bird" | "square";
export type SimulationMode = "slingshot" | "manual";

export const GRAVITIES: Record<GravityKey, number> = {
  Earth: 9.8,
  Moon: 1.6,
  Mars: 3.7,
};

export const PIXELS_PER_M = 6;

// Projectile rendering properties
export const PROJECTILE_STYLES: Record<
  ProjectileType,
  {
    color: string;
    glowColor: string;
    radius: number;
    label: string;
  }
> = {
  ball: {
    color: "#ffd166",
    glowColor: "#ff8c42",
    radius: 10,
    label: "Ball",
  },
  bird: {
    color: "#ff6b6b",
    glowColor: "#ff6b6b",
    radius: 12,
    label: "Bird",
  },
  square: {
    color: "#7dd3fc",
    glowColor: "#38bdf8",
    radius: 9,
    label: "Square",
  },
};

// ============= Physics Calculations =============

/**
 * Calculate horizontal range
 * R = v² * sin(2θ) / g
 */
export function calculateRange(v: number, angleDeg: number, g: number): number {
  const a = (angleDeg * Math.PI) / 180;
  return (v * v * Math.sin(2 * a)) / g;
}

/**
 * Calculate maximum height
 * H = v² * sin²(θ) / (2g)
 */
export function calculateMaxHeight(v: number, angleDeg: number, g: number): number {
  const a = (angleDeg * Math.PI) / 180;
  return (v * v * Math.sin(a) ** 2) / (2 * g);
}

/**
 * Calculate time of flight
 * T = 2v * sin(θ) / g
 */
export function calculateTimeOfFlight(v: number, angleDeg: number, g: number): number {
  const a = (angleDeg * Math.PI) / 180;
  return (2 * v * Math.sin(a)) / g;
}

/**
 * Generate trajectory preview points
 * Returns array of {x, y} points representing parabolic path
 */
export function trajectoryPoints(
  v: number,
  angleDeg: number,
  g: number,
  steps: number = 60,
): Array<{ x: number; y: number }> {
  const a = (angleDeg * Math.PI) / 180;
  const tof = calculateTimeOfFlight(v, angleDeg, g);
  const points: Array<{ x: number; y: number }> = [];

  for (let i = 0; i <= steps; i++) {
    const t = (i / steps) * tof;
    const x = v * Math.cos(a) * t;
    const y = v * Math.sin(a) * t - 0.5 * g * t * t;
    points.push({ x, y });
  }

  return points;
}

/**
 * Calculate initial velocity components from power and angle
 */
export function getVelocityComponents(power: number, angleDeg: number): { vx: number; vy: number } {
  const a = (angleDeg * Math.PI) / 180;
  return {
    vx: power * Math.cos(a),
    vy: -power * Math.sin(a), // Negative because canvas Y increases downward
  };
}

/**
 * Calculate impact speed from velocity components
 */
export function calculateImpactSpeed(vx: number, vy: number): number {
  return Math.hypot(vx, vy);
}

/**
 * Clamp angle to realistic range
 */
export function clampAngle(angle: number): number {
  return Math.max(0, Math.min(90, angle));
}

/**
 * Clamp power to valid range
 */
export function clampPower(power: number): number {
  return Math.max(0, Math.min(100, power));
}

/**
 * Clamp gravity to valid range
 */
export function clampGravity(gravity: number): number {
  return Math.max(1, Math.min(25, gravity));
}

/**
 * Convert angle from radians to degrees
 */
export function radToDeg(rad: number): number {
  return (rad * 180) / Math.PI;
}

/**
 * Convert angle from degrees to radians
 */
export function degToRad(deg: number): number {
  return (deg * Math.PI) / 180;
}
