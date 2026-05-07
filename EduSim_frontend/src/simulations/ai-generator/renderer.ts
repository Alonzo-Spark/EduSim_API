/**
 * Simulation Canvas Renderer
 * Renders objects onto canvas
 */

import { PhysicsObject } from "@/types/simulation";
import { SimulationState } from "./engine";

export class SimulationRenderer {
  private canvas: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D;
  private trails: Map<string, [number, number][]> = new Map();
  private maxTrailLength: number = 100;

  constructor(canvas: HTMLCanvasElement) {
    this.canvas = canvas;
    const ctx = canvas.getContext("2d");
    if (!ctx) throw new Error("Could not get canvas context");
    this.ctx = ctx;
    this.setupCanvas();
  }

  private setupCanvas(): void {
    const rect = this.canvas.getBoundingClientRect();
    this.canvas.width = rect.width * window.devicePixelRatio;
    this.canvas.height = rect.height * window.devicePixelRatio;
    this.ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
  }

  /**
   * Render simulation state
   */
  render(state: SimulationState, environment: any): void {
    const width = this.canvas.width / window.devicePixelRatio;
    const height = this.canvas.height / window.devicePixelRatio;

    // Clear canvas with gradient background
    this.drawBackground(width, height, environment.background);

    // Draw all objects
    state.objects.forEach((obj) => {
      if (obj.trail) {
        this.updateTrail(obj);
        this.drawTrail(obj);
      }
      this.drawObject(obj);
    });

    // Draw info
    this.drawInfo(state, width, height);
  }

  private drawBackground(width: number, height: number, background: string): void {
    // Create gradient based on background type
    const gradient = this.ctx.createLinearGradient(0, 0, width, height);

    switch (background) {
      case "space":
        gradient.addColorStop(0, "#0a0e27");
        gradient.addColorStop(1, "#1a1f3a");
        break;
      case "earth":
        gradient.addColorStop(0, "#87ceeb");
        gradient.addColorStop(1, "#90ee90");
        break;
      case "ocean":
        gradient.addColorStop(0, "#1e90ff");
        gradient.addColorStop(1, "#000080");
        break;
      case "laboratory":
        gradient.addColorStop(0, "#f0f0f0");
        gradient.addColorStop(1, "#e0e0e0");
        break;
      case "vacuum":
        gradient.addColorStop(0, "#1a1a2e");
        gradient.addColorStop(1, "#16213e");
        break;
      default:
        gradient.addColorStop(0, "#0f172a");
        gradient.addColorStop(1, "#1e293b");
    }

    this.ctx.fillStyle = gradient;
    this.ctx.fillRect(0, 0, width, height);
  }

  private drawObject(obj: PhysicsObject): void {
    const [x, y] = obj.position;
    const color = obj.color || "#3b82f6";

    this.ctx.save();
    this.ctx.translate(x, y);
    this.ctx.rotate(obj.rotation || 0);

    switch (obj.type) {
      case "ball":
      case "planet":
        this.drawCircle(color, obj.radius || 10);
        break;

      case "projectile":
        this.drawProjectile(color, obj.radius || 5);
        break;

      case "block":
        this.drawBlock(color, obj.width || 30, obj.height || 20);
        break;

      case "pendulum":
        this.drawPendulum(obj);
        break;

      case "spring":
        this.drawSpring(obj);
        break;

      case "wave":
        this.drawWave(obj);
        break;

      default:
        this.drawCircle(color, 5);
    }

    this.ctx.restore();

    // Draw label if present
    if (obj.label) {
      this.ctx.fillStyle = "#e2e8f0";
      this.ctx.font = "12px monospace";
      this.ctx.textAlign = "center";
      this.ctx.fillText(obj.label, x, y - (obj.radius || 10) - 10);
    }
  }

  private drawCircle(color: string, radius: number): void {
    // Main circle
    this.ctx.fillStyle = color;
    this.ctx.beginPath();
    this.ctx.arc(0, 0, radius, 0, Math.PI * 2);
    this.ctx.fill();

    // Glow effect
    this.ctx.strokeStyle = color + "80";
    this.ctx.lineWidth = 2;
    this.ctx.beginPath();
    this.ctx.arc(0, 0, radius + 3, 0, Math.PI * 2);
    this.ctx.stroke();

    // Highlight
    this.ctx.fillStyle = "rgba(255, 255, 255, 0.3)";
    this.ctx.beginPath();
    this.ctx.arc(-radius / 3, -radius / 3, radius / 3, 0, Math.PI * 2);
    this.ctx.fill();
  }

  private drawProjectile(color: string, radius: number): void {
    // Projectile with trail indicator
    this.ctx.fillStyle = color;
    this.ctx.beginPath();
    this.ctx.arc(0, 0, radius, 0, Math.PI * 2);
    this.ctx.fill();

    // Direction indicator
    this.ctx.strokeStyle = color;
    this.ctx.lineWidth = 1;
    this.ctx.beginPath();
    this.ctx.moveTo(0, 0);
    this.ctx.lineTo(radius * 1.5, 0);
    this.ctx.stroke();
  }

  private drawBlock(color: string, width: number, height: number): void {
    this.ctx.fillStyle = color;
    this.ctx.fillRect(-width / 2, -height / 2, width, height);

    // Border
    this.ctx.strokeStyle = color + "80";
    this.ctx.lineWidth = 1;
    this.ctx.strokeRect(-width / 2, -height / 2, width, height);
  }

  private drawPendulum(obj: PhysicsObject): void {
    const length = obj.length || 100;
    const angle = obj.angle || 0;
    const bobRadius = obj.radius || 8;

    // String
    this.ctx.strokeStyle = "#94a3b8";
    this.ctx.lineWidth = 2;
    this.ctx.beginPath();
    this.ctx.moveTo(0, 0);
    this.ctx.lineTo(length * Math.sin(angle), length * Math.cos(angle));
    this.ctx.stroke();

    // Bob
    this.ctx.save();
    this.ctx.translate(length * Math.sin(angle), length * Math.cos(angle));
    this.drawCircle(obj.color || "#f59e0b", bobRadius);
    this.ctx.restore();

    // Pivot
    this.ctx.fillStyle = "#64748b";
    this.ctx.beginPath();
    this.ctx.arc(0, 0, 3, 0, Math.PI * 2);
    this.ctx.fill();
  }

  private drawSpring(obj: PhysicsObject): void {
    const restLength = obj.restLength || 100;
    const coils = 8;
    const coilWidth = 10;

    this.ctx.strokeStyle = obj.color || "#06b6d4";
    this.ctx.lineWidth = 2;
    this.ctx.beginPath();

    for (let i = 0; i <= coils; i++) {
      const x = (i / coils) * restLength;
      const y = i % 2 === 0 ? coilWidth / 2 : -coilWidth / 2;
      if (i === 0) {
        this.ctx.moveTo(x, y);
      } else {
        this.ctx.lineTo(x, y);
      }
    }

    this.ctx.stroke();
  }

  private drawWave(obj: PhysicsObject): void {
    const amplitude = obj.radius || 20;
    const wavelength = 60;
    const time = Date.now() / 1000;

    this.ctx.strokeStyle = obj.color || "#3b82f6";
    this.ctx.lineWidth = 2;
    this.ctx.beginPath();

    for (let x = -50; x <= 50; x += 2) {
      const y = amplitude * Math.sin((x / wavelength) * Math.PI * 2 - time * 2);
      if (x === -50) {
        this.ctx.moveTo(x, y);
      } else {
        this.ctx.lineTo(x, y);
      }
    }

    this.ctx.stroke();
  }

  private updateTrail(obj: PhysicsObject): void {
    const [x, y] = obj.position;
    const id = obj.id || "";

    if (!this.trails.has(id)) {
      this.trails.set(id, []);
    }

    const trail = this.trails.get(id)!;
    trail.push([x, y]);

    if (trail.length > this.maxTrailLength) {
      trail.shift();
    }
  }

  private drawTrail(obj: PhysicsObject): void {
    const id = obj.id || "";
    const trail = this.trails.get(id);

    if (!trail || trail.length < 2) return;

    this.ctx.strokeStyle = (obj.color || "#3b82f6") + "40";
    this.ctx.lineWidth = 1;
    this.ctx.beginPath();
    this.ctx.moveTo(trail[0][0], trail[0][1]);

    for (let i = 1; i < trail.length; i++) {
      this.ctx.lineTo(trail[i][0], trail[i][1]);
    }

    this.ctx.stroke();
  }

  private drawInfo(state: SimulationState, width: number, height: number): void {
    this.ctx.fillStyle = "#94a3b8";
    this.ctx.font = "12px monospace";
    this.ctx.textAlign = "left";

    const info = [
      `Time: ${state.time.toFixed(2)}s`,
      `Objects: ${state.objects.length}`,
      `Gravity: ${state.gravity.toFixed(1)} m/s²`,
      `Speed: ${state.timeScale.toFixed(1)}x`,
      state.paused ? "PAUSED" : "RUNNING",
    ];

    info.forEach((text, idx) => {
      this.ctx.fillText(text, 10, 20 + idx * 18);
    });
  }

  /**
   * Handle canvas resize
   */
  resize(): void {
    this.setupCanvas();
  }

  /**
   * Clear trails
   */
  clearTrails(): void {
    this.trails.clear();
  }
}
