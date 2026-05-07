/**
 * Simulation JSON Schema Types
 * Defines the structure for AI-generated simulations
 */

export type ObjectType =
  | "ball"
  | "planet"
  | "pendulum"
  | "spring"
  | "block"
  | "wave"
  | "projectile"
  | "liquid";

export type Behavior =
  | "gravity"
  | "collision"
  | "orbit"
  | "friction"
  | "bouncing"
  | "oscillation"
  | "damping"
  | "drag";

export type EnvironmentBackground =
  | "space"
  | "earth"
  | "ocean"
  | "laboratory"
  | "vacuum"
  | "custom";

// Physics object configuration
export interface PhysicsObject {
  id?: string;
  type: ObjectType;
  color?: string;
  position: [number, number] | [number, number, number]; // [x, y] or [x, y, z]
  velocity?: [number, number] | [number, number, number];
  radius?: number;
  mass?: number;
  width?: number;
  height?: number;
  rotation?: number;
  rotationVelocity?: number;
  physics?: {
    bounce?: boolean;
    restitution?: number;
    friction?: number;
    static?: boolean;
    gravity?: boolean;
    collisions?: boolean;
  };
  // Specific to pendulum
  length?: number;
  angle?: number;
  angularVelocity?: number;

  // Specific to spring
  restLength?: number;
  springConstant?: number;
  damping?: number;

  // Specific to orbit
  orbitRadius?: number;
  orbitSpeed?: number;

  // For projectile
  velocityMagnitude?: number;

  label?: string;
  trail?: boolean;
  trailLength?: number;
}

export interface Environment {
  gravity: number; // m/s²
  background: EnvironmentBackground;
  width?: number;
  height?: number;
  timeScale?: number;
  friction?: number;
  airResistance?: number;
  boundaryType?: "wrap" | "bounce" | "stop";
}

export interface SimulationConfig {
  environment: Environment;
  objects: PhysicsObject[];
  duration?: number;
  fps?: number;
  description?: string;
  topic?: string;
  educationalContext?: string;
}

// Validation and type guards
export function isValidObjectType(type: any): type is ObjectType {
  return ["ball", "planet", "pendulum", "spring", "block", "wave", "projectile", "liquid"].includes(
    type,
  );
}

export function isValidBehavior(behavior: any): behavior is Behavior {
  return [
    "gravity",
    "collision",
    "orbit",
    "friction",
    "bouncing",
    "oscillation",
    "damping",
    "drag",
  ].includes(behavior);
}

export function validateSimulationConfig(config: any): config is SimulationConfig {
  if (!config || typeof config !== "object") return false;
  if (!config.environment || !Array.isArray(config.objects)) return false;
  if (!Array.isArray(config.objects)) return false;

  return config.objects.every(
    (obj: any) =>
      obj.type &&
      isValidObjectType(obj.type) &&
      Array.isArray(obj.position) &&
      obj.position.length >= 2,
  );
}
