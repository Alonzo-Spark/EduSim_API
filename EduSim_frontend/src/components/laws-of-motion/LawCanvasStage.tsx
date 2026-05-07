import { useEffect, useRef } from "react";

export interface LawCanvasEngine {
  step(deltaSeconds: number): void;
  render(ctx: CanvasRenderingContext2D, width: number, height: number): void;
  pointerDown?(x: number, y: number): void;
  pointerMove?(x: number, y: number): void;
  pointerUp?(): void;
}

interface LawCanvasStageProps {
  engine: LawCanvasEngine;
  onFrame?: () => void;
  className?: string;
}

/**
 * Stable canvas rendering stage.
 *
 * Key stabilisation techniques:
 * - The useEffect runs exactly ONCE (empty dep array). The animation loop
 *   never restarts due to prop changes.
 * - Engine and onFrame are accessed via refs so the loop always uses the
 *   latest values without being a dependency.
 * - ResizeObserver only resizes the backing store; it never tears down and
 *   recreates the loop.
 */
export function LawCanvasStage({ engine, onFrame, className }: LawCanvasStageProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Stable refs so the RAF loop always calls the latest engine / callback
  // without any dep-array changes that would restart the loop.
  const engineRef = useRef<LawCanvasEngine>(engine);
  const onFrameRef = useRef<(() => void) | undefined>(onFrame);

  // Keep refs current on every render – this is safe because refs don't
  // trigger re-renders or useEffect re-runs.
  engineRef.current = engine;
  onFrameRef.current = onFrame;

  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;

    if (!canvas || !container) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let width = 0;
    let height = 0;
    let rafId = 0;
    let previous = performance.now();
    let resizePending = false;

    // ──────────────────────────────────────────────────────────────────
    // Resize – only update the backing-store dimensions; do NOT restart
    // the animation loop.  We debounce with rAF to avoid "jitter" when
    // the browser fires many resize events in a row.
    // ──────────────────────────────────────────────────────────────────
    const applyResize = () => {
      resizePending = false;
      const rect = container.getBoundingClientRect();
      if (rect.width === 0) return;
      width = rect.width;
      height = Math.max(420, Math.min(720, rect.width * 0.58));
      const dpr = window.devicePixelRatio || 1;
      const pw = Math.floor(width * dpr);
      const ph = Math.floor(height * dpr);
      // Only mutate if size actually changed to avoid unnecessary resets
      if (canvas.width !== pw || canvas.height !== ph) {
        canvas.width = pw;
        canvas.height = ph;
        canvas.style.width = `${width}px`;
        canvas.style.height = `${height}px`;
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      }
    };

    const scheduleResize = () => {
      if (!resizePending) {
        resizePending = true;
        requestAnimationFrame(applyResize);
      }
    };

    const resizeObserver = new ResizeObserver(scheduleResize);
    resizeObserver.observe(container);
    applyResize(); // initial sizing

    // ──────────────────────────────────────────────────────────────────
    // Animation loop – runs forever until the component unmounts.
    // Uses engineRef so it always calls the current engine instance
    // without restarting.
    // ──────────────────────────────────────────────────────────────────
    const animate = (now: number) => {
      const delta = Math.min(0.032, (now - previous) / 1000);
      previous = now;

      const e = engineRef.current;
      e.step(delta);
      ctx.clearRect(0, 0, width, height);
      e.render(ctx, width, height);
      onFrameRef.current?.();

      rafId = requestAnimationFrame(animate);
    };

    rafId = requestAnimationFrame(animate);

    // ──────────────────────────────────────────────────────────────────
    // Pointer events
    // ──────────────────────────────────────────────────────────────────
    const toLocal = (e: PointerEvent) => {
      const rect = canvas.getBoundingClientRect();
      return { x: e.clientX - rect.left, y: e.clientY - rect.top };
    };

    const onDown = (e: PointerEvent) => {
      const p = toLocal(e);
      canvas.setPointerCapture(e.pointerId);
      engineRef.current.pointerDown?.(p.x, p.y);
    };
    const onMove = (e: PointerEvent) => {
      const p = toLocal(e);
      engineRef.current.pointerMove?.(p.x, p.y);
    };
    const onUp = () => engineRef.current.pointerUp?.();

    canvas.addEventListener("pointerdown", onDown);
    canvas.addEventListener("pointermove", onMove);
    canvas.addEventListener("pointerup", onUp);
    canvas.addEventListener("pointercancel", onUp);

    return () => {
      resizeObserver.disconnect();
      cancelAnimationFrame(rafId);
      canvas.removeEventListener("pointerdown", onDown);
      canvas.removeEventListener("pointermove", onMove);
      canvas.removeEventListener("pointerup", onUp);
      canvas.removeEventListener("pointercancel", onUp);
    };
    // ⚠️  INTENTIONALLY empty dep array – the loop must start once and
    //    run forever.  Prop changes are handled via refs above.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div ref={containerRef} className={className ?? "w-full h-full"}>
      <canvas ref={canvasRef} className="block rounded-2xl w-full h-full" />
    </div>
  );
}
