/**
 * Simulation Engine
 * Handles physics calculations and object updates
 */

import { SimulationConfig, PhysicsObject } from "@/types/simulation";

export interface SimulationState {
  objects: PhysicsObject[];
  time: number;
  paused: boolean;
  gravity: number;
  timeScale: number;
}

export class SimulationEngine {
  private config: SimulationConfig;
  private state: SimulationState;
  private frameCount: number = 0;
  private lastFrameTime: number = 0;
  private animationId: number | null = null;
  private updateCallback: ((state: SimulationState) => void) | null = null;

  constructor(config: SimulationConfig) {
    this.config = config;
    this.state = {
      objects: this.initializeObjects(config.objects),
      time: 0,
      paused: false,
      gravity: config.environment.gravity,
      timeScale: config.environment.timeScale || 1,
    };
  }

  private initializeObjects(objects: PhysicsObject[]): PhysicsObject[] {
    return objects.map((obj, idx) => ({
      ...obj,
      id: obj.id || `obj-${idx}`,
      velocity: obj.velocity || [0, 0],
      mass: obj.mass || 1,
      rotation: obj.rotation || 0,
      rotationVelocity: obj.rotationVelocity || 0,
    }));
  }

  /**
   * Update simulation for next frame
   */
  private update(deltaTime: number): void {
    if (this.state.paused) return;

    const dt = deltaTime * this.state.timeScale;
    const gravity = this.state.gravity;

    this.state.objects = this.state.objects.map((obj) => {
      const updatedObj = { ...obj };
      const vel = obj.velocity || [0, 0];
      const pos = obj.position;

      switch (obj.type) {
        case "ball":
          return this.updateBall(updatedObj, vel, pos, gravity, dt);

        case "projectile":
          return this.updateProjectile(updatedObj, vel, pos, gravity, dt);

        case "planet":
          return this.updatePlanet(updatedObj, vel, pos, gravity, dt);

        case "pendulum":
          return this.updatePendulum(updatedObj, gravity, dt);

        case "spring":
          return this.updateSpring(updatedObj, gravity, dt);

        case "block":
          return this.updateBlock(updatedObj, vel, pos, gravity, dt);

        default:
          return updatedObj;
      }
    });

    this.state.time += deltaTime;
  }

  private updateBall(
    obj: PhysicsObject,
    vel: number[],
    pos: number[],
    gravity: number,
    dt: number,
  ): PhysicsObject {
    let [vx, vy] = vel;
    let [x, y] = pos;

    // Apply gravity
    if (!obj.physics?.static) {
      vy += gravity * dt;
    }

    // Apply friction/air resistance
    const airResistance = this.config.environment.airResistance || 0.01;
    vx *= 1 - airResistance;
    vy *= 1 - airResistance;

    // Update position
    x += vx * dt;
    y += vy * dt;

    // Bounce off boundaries
    const width = this.config.environment.width || 800;
    const height = this.config.environment.height || 600;
    const radius = obj.radius || 5;
    const restitution = obj.physics?.restitution ?? 0.8;

    if (obj.physics?.bounce !== false) {
      if (x - radius < 0) {
        x = radius;
        vx *= -restitution;
      }
      if (x + radius > width) {
        x = width - radius;
        vx *= -restitution;
      }
      if (y + radius > height) {
        y = height - radius;
        vy *= -restitution;
      }
      if (y - radius < 0) {
        y = radius;
        vy *= -restitution;
      }
    }

    return {
      ...obj,
      position: [x, y],
      velocity: [vx, vy],
    };
  }

  private updateProjectile(
    obj: PhysicsObject,
    vel: number[],
    pos: number[],
    gravity: number,
    dt: number,
  ): PhysicsObject {
    let [vx, vy] = vel;
    let [x, y] = pos;

    // Apply gravity
    vy += gravity * dt;

    // Apply air resistance
    const dragCoefficient = 0.02;
    const speed = Math.sqrt(vx * vx + vy * vy);
    if (speed > 0) {
      vx *= 1 - dragCoefficient * dt;
      vy *= 1 - dragCoefficient * dt;
    }

    // Update position
    x += vx * dt;
    y += vy * dt;

    // Stop if hits ground
    const height = this.config.environment.height || 600;
    if (y > height) {
      return {
        ...obj,
        position: [x, height],
        velocity: [0, 0],
      };
    }

    return {
      ...obj,
      position: [x, y],
      velocity: [vx, vy],
    };
  }

  private updatePlanet(
    obj: PhysicsObject,
    vel: number[],
    pos: number[],
    gravity: number,
    dt: number,
  ): PhysicsObject {
    // For orbital motion - simplified circular orbit
    if (obj.orbitSpeed && obj.orbitRadius) {
      const centerX = this.config.environment.width || 800 / 2;
      const centerY = this.config.environment.height || 600 / 2;

      const angle = Math.atan2(pos[1] - centerY, pos[0] - centerX) + obj.orbitSpeed * dt;
      const x = centerX + obj.orbitRadius * Math.cos(angle);
      const y = centerY + obj.orbitRadius * Math.sin(angle);

      return {
        ...obj,
        position: [x, y],
        rotation: (obj.rotation || 0) + 0.5 * dt,
      };
    }

    return obj;
  }

  private updatePendulum(obj: PhysicsObject, gravity: number, dt: number): PhysicsObject {
    const length = obj.length || 100;
    let angle = obj.angle || 0;
    let angularVelocity = obj.angularVelocity || 0;

    // Simple pendulum physics: θ'' = -(g/L) * sin(θ)
    const angularAcceleration = -(gravity / length) * Math.sin(angle);

    // Apply damping
    const damping = obj.damping ?? 0.02;
    angularVelocity *= 1 - damping;
    angularVelocity += angularAcceleration * dt;
    angle += angularVelocity * dt;

    // Calculate end position
    const centerX = this.config.environment.width || 800 / 2;
    const centerY = 50; // Top of canvas
    const x = centerX + length * Math.sin(angle);
    const y = centerY + length * Math.cos(angle);

    return {
      ...obj,
      angle,
      angularVelocity,
      position: [x, y],
      rotation: angle,
    };
  }

  private updateSpring(obj: PhysicsObject, gravity: number, dt: number): PhysicsObject {
    const restLength = obj.restLength || 100;
    const springConstant = obj.springConstant || 1;
    const damping = obj.damping || 0.1;

    // This would need a reference point - simplified for now
    return obj;
  }

  private updateBlock(
    obj: PhysicsObject,
    vel: number[],
    pos: number[],
    gravity: number,
    dt: number,
  ): PhysicsObject {
    let [vx, vy] = vel;
    let [x, y] = pos;

    // Apply gravity
    vy += gravity * dt;

    // Friction
    const friction = 0.1;
    vx *= 1 - friction;

    // Update position
    x += vx * dt;
    y += vy * dt;

    // Collision with ground
    const height = this.config.environment.height || 600;
    const blockHeight = obj.height || 20;

    if (y + blockHeight > height) {
      y = height - blockHeight;
      vy *= -(obj.physics?.restitution ?? 0.3);
      vx *= 0.8; // Friction on bounce
    }

    return {
      ...obj,
      position: [x, y],
      velocity: [vx, vy],
    };
  }

  /**
   * Start simulation
   */
  start(updateCallback: (state: SimulationState) => void): void {
    this.updateCallback = updateCallback;
    this.lastFrameTime = performance.now();
    this.animate();
  }

  /**
   * Animation loop
   */
  private animate = (): void => {
    const currentTime = performance.now();
    const deltaTime = Math.min((currentTime - this.lastFrameTime) / 1000, 0.1); // Cap at 100ms

    this.update(deltaTime);
    this.lastFrameTime = currentTime;

    if (this.updateCallback) {
      this.updateCallback(this.state);
    }

    // Continue if not stopped
    if (this.animationId !== null) {
      this.animationId = requestAnimationFrame(this.animate);
    }
  };

  /**
   * Stop simulation
   */
  stop(): void {
    if (this.animationId !== null) {
      cancelAnimationFrame(this.animationId);
      this.animationId = null;
    }
  }

  /**
   * Pause/Resume
   */
  pause(): void {
    this.state.paused = true;
  }

  resume(): void {
    this.state.paused = false;
  }

  /**
   * Reset to initial state
   */
  reset(): void {
    this.state = {
      objects: this.initializeObjects(this.config.objects),
      time: 0,
      paused: false,
      gravity: this.config.environment.gravity,
      timeScale: this.config.environment.timeScale || 1,
    };
  }

  /**
   * Update gravity
   */
  setGravity(gravity: number): void {
    this.state.gravity = gravity;
  }

  /**
   * Update time scale
   */
  setTimeScale(timeScale: number): void {
    this.state.timeScale = Math.max(0.1, Math.min(2, timeScale));
  }

  /**
   * Get current state
   */
  getState(): SimulationState {
    return { ...this.state };
  }

  /**
   * Update config
   */
  setConfig(config: SimulationConfig): void {
    this.config = config;
    this.reset();
  }
}
