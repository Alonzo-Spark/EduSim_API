import React, { useEffect, useRef, useState, useCallback } from 'react';
import type { SandboxRuntime } from '../engine/runtime';
import type { RuntimeObject } from '../types/RuntimeObject';
import type { Body } from 'matter-js';
import { ConstraintRegistry } from '../constraints/constraintRegistry';
import type { ConstraintRenderer } from '../constraints/constraintRenderer';
import { ObservableEngine } from '../observables/observableEngine';
import { RuntimeStore } from '../state/runtimeStore';
import { PropertyController } from '../properties/propertyController';
import { PropertyPanel } from '../ui/PropertyPanel';


// ─── Constants ────────────────────────────────────────────────────────────────

type GravityPreset = 'zero' | 'moon' | 'earth' | 'jupiter';

const GRAVITY_VALUES: Record<GravityPreset, number> = {
  zero: 0, moon: 0.16, earth: 1, jupiter: 2.53,
};

const PALETTE = [
  { fill: 0x8b5cf6, stroke: 0xc084fc },
  { fill: 0x06b6d4, stroke: 0x67e8f9 },
  { fill: 0xf59e0b, stroke: 0xfcd34d },
  { fill: 0xec4899, stroke: 0xf9a8d4 },
  { fill: 0x10b981, stroke: 0x6ee7b7 },
  { fill: 0xf97316, stroke: 0xfdba74 },
  { fill: 0x6366f1, stroke: 0xa5b4fc },
  { fill: 0xeab308, stroke: 0xfde047 },
];

let _pi = 0;
let _uid = 0;
const nextColour = () => PALETTE[_pi++ % PALETTE.length];
const uid = (p: string) => `${p}-${++_uid}`;

// ─── Stable refs ─────────────────────────────────────────────────────────────

interface InteractionRefs {
  drag: import('../interactions/drag').DragController;
  selection: import('../interactions/selection').SelectionManager;
  controls: import('../interactions/controls').RuntimeControls;
}

// ─── Scene builder ────────────────────────────────────────────────────────────

async function buildScene(
  rt: SandboxRuntime,
  el: HTMLElement,
  interactions: InteractionRefs,
  constraintReg: ConstraintRegistry,
  store: RuntimeStore,
): Promise<Body[]> {
  const { createObject } = await import('../objects/objectFactory');
  const { createConstraint } = await import('../constraints/constraintFactory');

  rt.physics.clear(false);
  rt.sync.clear();
  constraintReg.clear();          // remove old constraints from world
  interactions.selection.clear();
  _uid = 0; _pi = 0;

  const vp = rt.renderer.getViewport();
  // Remove non-graphics children, while preserving constraint and observable overlays.
  for (let i = vp.children.length - 1; i >= 0; i--) {
    const child = vp.children[i];
    const meta = child as { _isConstraintOverlay?: boolean; _isObservableOverlay?: boolean };
    if (meta._isConstraintOverlay || meta._isObservableOverlay) continue;
    vp.removeChildAt(i);
  }

  vp.eventMode = 'passive';

  const W = el.clientWidth || 800;
  const H = el.clientHeight || 600;
  const dynamic: Body[] = [];

  const addStatic = (obj: RuntimeObject) => {
    vp.addChild(obj.display);
    rt.physics.addBodies(obj.body);
    rt.sync.register(obj.id, obj.body, obj.display);
  };

  const addDynamic = (obj: RuntimeObject) => {
    vp.addChild(obj.display);
    rt.physics.addBodies(obj.body);
    rt.sync.register(obj.id, obj.body, obj.display);
    interactions.selection.register(obj);
    store.addObject(obj);
    dynamic.push(obj.body);
  };

  const addConstraint = (cfg: Parameters<typeof createConstraint>[0]) => {
    constraintReg.add(createConstraint(cfg));
  };

  // ── Static boundaries ─────────────────────────────────────────────────────
  addStatic(createObject({
    id: 'ground', type: 'rectangle',
    x: W / 2, y: H - 40, width: W, height: 28,
    isStatic: true, fillColor: 0x1e293b, strokeColor: 0x334155, strokeWidth: 1,
  }));
  addStatic(createObject({
    id: 'wall-l', type: 'rectangle',
    x: -4, y: H / 2, width: 16, height: H * 2,
    isStatic: true, fillColor: 0x1e293b, strokeColor: 0x334155, strokeWidth: 1,
  }));
  addStatic(createObject({
    id: 'wall-r', type: 'rectangle',
    x: W + 4, y: H / 2, width: 16, height: H * 2,
    isStatic: true, fillColor: 0x1e293b, strokeColor: 0x334155, strokeWidth: 1,
  }));

  return dynamic;
}

// ─── Component ────────────────────────────────────────────────────────────────

export const SandboxCanvas: React.FC = () => {
  const mountRef = useRef<HTMLDivElement>(null);
  const runtimeRef = useRef<SandboxRuntime | null>(null);
  const storeRef = useRef<RuntimeStore | null>(null);
  const interactionRef = useRef<InteractionRefs | null>(null);
  const constraintRegRef = useRef<ConstraintRegistry | null>(null);
  const constraintRenRef = useRef<ConstraintRenderer | null>(null);
  const observableEngineRef = useRef<ObservableEngine | null>(null);
  const dynRef = useRef<Body[]>([]);

  const [running, setRunning] = useState(false);
  const [ready, setReady] = useState(false);
  const [bodyCount, setBodyCount] = useState(0);
  const [gravity, setGravity] = useState<GravityPreset>('earth');
  const [speed, setSpeed] = useState(1);
  const [selected, setSelected] = useState<RuntimeObject | null>(null);

  const propertyControllerRef = useRef<PropertyController | null>(null);
  const [propertyVersion, setPropertyVersion] = useState(0);
  const [telemetryTick, setTelemetryTick] = useState(0);

  // Newton Second Law HUD DOM refs
  const hudForceRef = useRef<HTMLSpanElement>(null);
  const hudMassRef = useRef<HTMLSpanElement>(null);
  const hudAccRef = useRef<HTMLSpanElement>(null);
  const hudFormulaRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let frameId: number;
    const updateHud = () => {
      const store = storeRef.current;
      const controller = propertyControllerRef.current;
      const obs = observableEngineRef.current;
      if (selected && store && controller) {
        const force = controller.getActiveForce(selected.id);
        const forceMag = Math.hypot(force.x, force.y);
        const mass = selected.body.mass;

        let accMag = 0;
        if (obs) {
          const metrics = obs.getObservables(selected.id);
          if (metrics && metrics.acceleration) {
            accMag = metrics.acceleration.magnitude;
          }
        }

        // Live text updates based directly on the applied force to isolate F = ma physics educationally
        const forceMagScaled = forceMag * 100;
        const accMagScaled = forceMagScaled / mass;

        if (hudForceRef.current) {
          hudForceRef.current.innerText = `${forceMagScaled.toFixed(1)} N`;
        }
        if (hudMassRef.current) {
          hudMassRef.current.innerText = `${mass.toFixed(1)} kg`;
        }
        if (hudAccRef.current) {
          hudAccRef.current.innerText = `${accMagScaled.toFixed(2)} m/s²`;
        }
        if (hudFormulaRef.current) {
          hudFormulaRef.current.innerHTML = `
            <div style="font-size: 15px; font-weight: 800; color: #fde047; text-shadow: 0 0 10px rgba(253,224,71,0.25);">
              F = m &middot; a
            </div>
            <div style="font-size: 11px; color: #94a3b8; margin-top: 4px; font-family: monospace; font-weight: 600;">
              ${forceMagScaled.toFixed(1)} N = ${mass.toFixed(1)} kg &times; ${accMagScaled.toFixed(2)} m/s&sup2;
            </div>
          `;
        }
      }
      frameId = requestAnimationFrame(updateHud);
    };

    frameId = requestAnimationFrame(updateHud);
    return () => cancelAnimationFrame(frameId);
  }, [selected, propertyVersion]);

  // Panel drag-and-drop state
  type PanelDragType = 'circle' | 'rectangle' | 'pendulum-rope' | 'pivot' | 'spring' | 'rope' | null;
  const panelDragRef = useRef<PanelDragType>(null);          // type being dragged
  const didDragRef = useRef(false);                        // suppresses onClick after a real drag
  const hoveredBodyRef = useRef<Body | null>(null);
  const [hoveredBodyId, setHoveredBodyId] = useState<string | null>(null);
  const [ghostPos, setGhostPos] = useState({ x: -999, y: -999 });
  const [isDragging, setIsDragging] = useState(false);
  const [isOverCanvas, setIsOverCanvas] = useState(false);

  // Check and snap a physics body to any nearby unconnected constraint receptors
  const checkConstraintSnapping = useCallback(async (newBody: Body) => {
    const rt = runtimeRef.current;
    const creg = constraintRegRef.current;
    if (!rt || !creg) return;

    const allBodies = rt.physics.getWorld().bodies;
    const sensors = allBodies.filter(b => b.label && b.label.startsWith('sensor-target:'));

    for (const sensor of sensors) {
      const dist = Math.hypot(newBody.position.x - sensor.position.x, newBody.position.y - sensor.position.y);
      if (dist < 100) { // generous snap tolerance so user can drop anywhere near the bottom of the rope
        const parts = sensor.label.split(':');
        const constraintId = parts[1];
        const syncDisplayId = parts[2]; // populated by spawnPendulumRope for its visible drop-zone
        const rc = creg.getAll().find(c => c.id === constraintId);
        if (rc) {
          // Relink constraint from temporary sensor bob to real dropped shape
          if (rc.constraint.bodyB === sensor) {
            rc.constraint.bodyB = newBody;
            if (rc.type === 'pivot') {
              const newDist = Math.hypot(rc.constraint.bodyA!.position.x - newBody.position.x, rc.constraint.bodyA!.position.y - newBody.position.y);
              rc.constraint.length = newDist;
            }
          } else if (rc.constraint.bodyA === sensor) {
            rc.constraint.bodyA = newBody;
          }

          // Remove physics sensor body
          rt.physics.removeBodies(sensor);

          // Remove the visible drop-zone display that was synced to the sensor
          if (syncDisplayId) {
            const pair = rt.sync.getPairs().get(syncDisplayId);
            if (pair) {
              pair.displayObject.parent?.removeChild(pair.displayObject);
              pair.displayObject.destroy();
              rt.sync.unregister(syncDisplayId);
            }
          }

          break;
        }
      }
    }
  }, []);

  // ── Mount ──────────────────────────────────────────────────────────────────

  useEffect(() => {
    const el = mountRef.current;
    if (!el) return;

    let alive = true;

    (async () => {
      try {
        const [
          { SandboxRuntime },
          { DragController },
          { SelectionManager },
          { RuntimeControls },
          { ConstraintRegistry },
          { ConstraintRenderer },
        ] = await Promise.all([
          import('../engine/runtime'),
          import('../interactions/drag'),
          import('../interactions/selection'),
          import('../interactions/controls'),
          import('../constraints/constraintRegistry'),
          import('../constraints/constraintRenderer'),
        ]);

        const rt = new SandboxRuntime();
        runtimeRef.current = rt;

        // Initialize centralized state management
        const store = new RuntimeStore();
        storeRef.current = store;
        store.setRuntimeState('uninitialized');

        const propertyController = new PropertyController(store, rt);
        propertyControllerRef.current = propertyController;

        // Force react update on property changes
        propertyController.subscribe('propertyChanged', () => {
          setPropertyVersion((v) => v + 1);
        });
        propertyController.subscribe('constraintUpdated', () => {
          setPropertyVersion((v) => v + 1);
        });



        // 1. Init renderer
        await rt.init(el);
        if (!alive) { rt.destroy(); return; }

        // 2. Interaction systems
        const canvas = rt.renderer.getApp().canvas as HTMLCanvasElement;
        const drag = new DragController(rt.physics.getEngine(), canvas);
        const selection = new SelectionManager();
        const controls = new RuntimeControls(rt);
        drag.enable();
        selection.onChange((obj) => {
          const prevId = storeRef.current?.getSelectedObjectId();
          setSelected(obj);
          if (obj) {
            store.setSelectedObject(obj.id);
            // Automatically upgrade observables for the selected object to render Force, Velocity, and Acceleration
            observableEngineRef.current?.registerObservable({
              objectId: obj.id,
              types: ['force', 'velocity', 'acceleration'],
              label: obj.metadata?.label || obj.id,
              color: 0xffffff,
            });
          } else {
            if (prevId) {
              // Restore default observables for the previous selected object
              if (prevId === 'falling-ball') {
                observableEngineRef.current?.registerObservable({
                  objectId: 'falling-ball',
                  types: ['velocity', 'acceleration'],
                  label: 'Falling object',
                  color: 0xf87171,
                });
              } else if (prevId === 'pendulum-bob') {
                observableEngineRef.current?.registerObservable({
                  objectId: 'pendulum-bob',
                  types: ['angularVelocity', 'velocity'],
                  label: 'Pendulum',
                  color: 0x8b5cf6,
                });
              } else if (prevId === 'spring-bob') {
                observableEngineRef.current?.registerObservable({
                  objectId: 'spring-bob',
                  types: ['velocity', 'kineticEnergy'],
                  label: 'Spring bob',
                  color: 0x10b981,
                });
              } else if (prevId === 'collision-ball-a') {
                observableEngineRef.current?.registerObservable({
                  objectId: 'collision-ball-a',
                  types: ['momentum', 'kineticEnergy'],
                  label: 'Collision A',
                  color: 0xfacc15,
                });
              } else if (prevId === 'collision-ball-b') {
                observableEngineRef.current?.registerObservable({
                  objectId: 'collision-ball-b',
                  types: ['momentum', 'kineticEnergy'],
                  label: 'Collision B',
                  color: 0x38bdf8,
                });
              } else if (!prevId.startsWith('ground') && !prevId.startsWith('wall')) {
                // If it's a generic spawned shape, unregister
                observableEngineRef.current?.unregisterObservable(prevId);
              }
            }
            store.clearSelection();
          }
        });
        rt.renderer.getApp().stage.eventMode = 'static';
        rt.renderer.getApp().stage.on('pointerdown', () => selection.deselect());
        interactionRef.current = { drag, selection, controls };

        // Real-time telemetry updating hook during active loop running
        rt.addHook({
          id: 'ui-telemetry-sync',
          afterStep: () => {
            if (store.getSelectedObject()) {
              setTelemetryTick((t) => t + 1);
            }
          },
        });

        // Listen for end of pointer drag gestures to snap dropped bodies onto constraints
        import('matter-js').then((Matter) => {
          const mc = drag.getMouseConstraint();
          if (mc) {
            Matter.Events.on(mc, 'enddrag', (event: any) => {
              if (event.body) {
                checkConstraintSnapping(event.body);
              }
            });
          }
        });

        // 3. Constraint systems
        const constraintReg = new ConstraintRegistry(rt.physics, store);
        const constraintRen = new ConstraintRenderer(rt);
        constraintRegRef.current = constraintReg;
        constraintRenRef.current = constraintRen;
        constraintRen.enable(() => constraintReg.getAll());

        const observableEngine = new ObservableEngine(rt, rt.sync, propertyController);
        observableEngine.enable();
        observableEngineRef.current = observableEngine;

        // 4. Build scene
        const dyn = await buildScene(rt, el, { drag, selection, controls }, constraintReg, store);
        if (!alive) { rt.destroy(); return; }

        dynRef.current = dyn;
        setBodyCount(dyn.length);

        observableEngineRef.current?.registerObservable({
          objectId: 'falling-ball',
          types: ['velocity', 'acceleration'],
          label: 'Falling object',
          color: 0xf87171,
        });
        observableEngineRef.current?.registerObservable({
          objectId: 'pendulum-bob',
          types: ['angularVelocity', 'velocity'],
          label: 'Pendulum',
          color: 0x8b5cf6,
        });
        observableEngineRef.current?.registerObservable({
          objectId: 'spring-bob',
          types: ['velocity', 'kineticEnergy'],
          label: 'Spring bob',
          color: 0x10b981,
        });
        observableEngineRef.current?.registerObservable({
          objectId: 'collision-ball-a',
          types: ['momentum', 'kineticEnergy'],
          label: 'Collision A',
          color: 0xfacc15,
        });
        observableEngineRef.current?.registerObservable({
          objectId: 'collision-ball-b',
          types: ['momentum', 'kineticEnergy'],
          label: 'Collision B',
          color: 0x38bdf8,
        });

        // 5. Start loop
        rt.start();
        store.setRuntimeState('running');
        setRunning(true);
        setReady(true);
      } catch (err) {
        console.error('[SandboxCanvas] init error:', err);
      }
    })();

    return () => {
      alive = false;
      interactionRef.current?.drag.destroy();
      interactionRef.current?.selection.clear();
      constraintRegRef.current?.clear();
      constraintRenRef.current?.destroy();
      observableEngineRef.current?.destroy();
      runtimeRef.current?.destroy();
      runtimeRef.current = null;
      storeRef.current = null;
      interactionRef.current = null;
      constraintRegRef.current = null;
      constraintRenRef.current = null;
      observableEngineRef.current = null;
      setReady(false);
      setRunning(false);
    };
  }, []);

  // ── Controls ───────────────────────────────────────────────────────────────

  const togglePlay = () => {
    const ctrl = interactionRef.current?.controls;
    if (!ctrl || !ready) return;
    if (running) { ctrl.pause(); setRunning(false); }
    else { ctrl.resume(); setRunning(true); }
  };

  const handleReset = useCallback(async () => {
    const rt = runtimeRef.current;
    const ia = interactionRef.current;
    const creg = constraintRegRef.current;
    const el = mountRef.current;
    const store = storeRef.current;
    if (!rt || !ia || !creg || !el || !store || !ready) return;

    const wasRunning = running;
    rt.pause();
    store.reset();
    const dyn = await buildScene(rt, el, ia, creg, store);
    dynRef.current = dyn;
    setBodyCount(dyn.length);
    setSelected(null);
    ia.controls.setGravity(GRAVITY_VALUES[gravity]);
    ia.controls.setSimulationSpeed(speed);
    if (wasRunning) {
      rt.start();
      store.setRuntimeState('running');
    }
  }, [ready, running, gravity, speed]);

  const spawnShape = useCallback(async (type: 'circle' | 'rectangle') => {
    const rt = runtimeRef.current;
    const ia = interactionRef.current;
    const el = mountRef.current;
    const store = storeRef.current;
    if (!rt || !ia || !el || !store || !ready) return;

    const { createObject } = await import('../objects/objectFactory');

    const W = el.clientWidth || 800;
    const x = 120 + Math.random() * (W - 240);
    const y = 40 + Math.random() * 50;
    const rest = 0.5 + Math.random() * 0.45;
    const size = 28 + Math.random() * 32;
    const { fill, stroke } = nextColour();
    const base = {
      x, y, restitution: rest, friction: 0.1, density: 0.002,
      fillColor: fill, strokeColor: stroke, strokeWidth: 2.5
    };

    const obj = type === 'circle'
      ? createObject({ id: uid('circle'), type: 'circle', radius: size / 2, ...base })
      : createObject({
        id: uid('rect'), type: 'rectangle', width: size, height: size,
        cornerRadius: 8, angle: Math.random() * Math.PI, ...base
      });

    rt.renderer.getViewport().addChild(obj.display);
    rt.physics.addBodies(obj.body);
    rt.sync.register(obj.id, obj.body, obj.display);
    ia.selection.register(obj);
    store.addObject(obj);
    dynRef.current.push(obj.body);
    setBodyCount(dynRef.current.length);
  }, [ready]);

  const blast = useCallback(async () => {
    if (!ready) return;
    const Matter = await import('matter-js');
    dynRef.current.forEach((b) => {
      Matter.Body.applyForce(b, b.position, { x: 0, y: -0.055 * b.mass });
      Matter.Body.setAngularVelocity(b, b.angularVelocity + (Math.random() - 0.5) * 0.3);
    });
  }, [ready]);

  const push = useCallback(async (dir: 'left' | 'right') => {
    if (!ready) return;
    const Matter = await import('matter-js');
    const fx = (dir === 'left' ? -1 : 1) * 0.028;
    dynRef.current.forEach((b) => Matter.Body.applyForce(b, b.position, { x: fx * b.mass, y: 0 }));
  }, [ready]);

  const changeGravity = (preset: GravityPreset) => {
    setGravity(preset);
    propertyControllerRef.current?.updateGlobalGravity(GRAVITY_VALUES[preset]);
  };

  const changeSpeed = (val: number) => {
    setSpeed(val);
    interactionRef.current?.controls.setSimulationSpeed(val);
  };

  // ── Panel drag-and-drop ────────────────────────────────────────────────────

  // Connect constraint to existing body, or spawn new complete system
  const spawnConstraintAt = useCallback(async (
    type: 'pivot' | 'spring' | 'rope',
    canvasX: number,
    canvasY: number,
    hoveredBody: Body | null,
  ) => {
    const rt = runtimeRef.current;
    const ia = interactionRef.current;
    const creg = constraintRegRef.current;
    const store = storeRef.current;
    if (!rt || !ia || !creg || !store || !ready) return;

    const { createObject } = await import('../objects/objectFactory');
    const { createConstraint } = await import('../constraints/constraintFactory');
    const Matter = await import('matter-js');
    const vp = rt.renderer.getViewport();

    const constraintId = uid('constraint');

    if (type === 'pivot') {
      if (hoveredBody) {
        const dist = Math.hypot(hoveredBody.position.x - canvasX, hoveredBody.position.y - canvasY);
        creg.add(createConstraint({
          id: constraintId,
          type: 'pivot',
          body: hoveredBody,
          anchor: { x: canvasX, y: canvasY },
          length: dist > 10 ? dist : 100,
          stiffness: 1,
          damping: 0.002,
        }));
      } else {
        // Spawn standalone ceiling anchor peg
        const pin = createObject({
          id: uid('pivot-pin'), type: 'circle',
          x: canvasX, y: canvasY, radius: 6,
          isStatic: true, fillColor: 0x334155, strokeColor: 0x475569, strokeWidth: 1,
        });
        vp.addChild(pin.display);
        rt.physics.addBodies(pin.body);
        rt.sync.register(pin.id, pin.body, pin.display);

        // Spawn a lightweight swinging receptor sensor
        const sensor = Matter.Bodies.circle(canvasX, canvasY + 120, 6, {
          isSensor: true,
          label: `sensor-target:${constraintId}`,
          density: 0.001,
          frictionAir: 0.05,
        });
        rt.physics.addBodies(sensor);

        creg.add(createConstraint({
          id: constraintId,
          type: 'pivot',
          body: sensor,
          anchor: { x: canvasX, y: canvasY },
          length: 120,
          stiffness: 1,
          damping: 0.002,
        }));
      }
    } else if (type === 'spring') {
      if (hoveredBody) {
        const anchorX = hoveredBody.position.x;
        const anchorY = Math.max(20, hoveredBody.position.y - 120);

        const ceiling = createObject({
          id: uid('spring-anchor'), type: 'rectangle',
          x: anchorX, y: anchorY, width: 30, height: 10,
          isStatic: true, fillColor: 0x1e293b, strokeColor: 0x334155, strokeWidth: 1,
        });
        vp.addChild(ceiling.display);
        rt.physics.addBodies(ceiling.body);
        rt.sync.register(ceiling.id, ceiling.body, ceiling.display);

        creg.add(createConstraint({
          id: constraintId,
          type: 'spring',
          bodyA: ceiling.body, bodyB: hoveredBody,
          length: 100, stiffness: 0.02, damping: 0.01,
        }));
      } else {
        // Spawn standalone spring hanger ceiling block
        const ceiling = createObject({
          id: uid('spring-anchor'), type: 'rectangle',
          x: canvasX, y: canvasY, width: 30, height: 10,
          isStatic: true, fillColor: 0x1e293b, strokeColor: 0x334155, strokeWidth: 1,
        });
        vp.addChild(ceiling.display);
        rt.physics.addBodies(ceiling.body);
        rt.sync.register(ceiling.id, ceiling.body, ceiling.display);

        // Spawn a lightweight bouncing receptor sensor
        const sensor = Matter.Bodies.circle(canvasX, canvasY + 100, 6, {
          isSensor: true,
          label: `sensor-target:${constraintId}`,
          density: 0.001,
          frictionAir: 0.05,
        });
        rt.physics.addBodies(sensor);

        creg.add(createConstraint({
          id: constraintId,
          type: 'spring',
          bodyA: ceiling.body, bodyB: sensor,
          length: 100, stiffness: 0.02, damping: 0.01,
        }));
      }
    } else if (type === 'rope') {
      if (hoveredBody) {
        const anchorX = hoveredBody.position.x;
        const anchorY = Math.max(20, hoveredBody.position.y - 100);

        const anchor = createObject({
          id: uid('rope-anchor'), type: 'circle',
          x: anchorX, y: anchorY, radius: 5,
          isStatic: true, fillColor: 0x334155, strokeColor: 0x475569, strokeWidth: 1,
        });
        vp.addChild(anchor.display);
        rt.physics.addBodies(anchor.body);
        rt.sync.register(anchor.id, anchor.body, anchor.display);

        creg.add(createConstraint({
          id: constraintId,
          type: 'rope',
          bodyA: anchor.body, bodyB: hoveredBody,
          length: Math.abs(hoveredBody.position.y - anchorY), stiffness: 0.9,
        }));
      } else {
        // Spawn standalone rope hanger
        const anchor = createObject({
          id: uid('rope-anchor'), type: 'circle',
          x: canvasX, y: canvasY, radius: 5,
          isStatic: true, fillColor: 0x334155, strokeColor: 0x475569, strokeWidth: 1,
        });
        vp.addChild(anchor.display);
        rt.physics.addBodies(anchor.body);
        rt.sync.register(anchor.id, anchor.body, anchor.display);

        let prevBody = anchor.body;
        const ropeSegL = 50;

        // Spawn first two physical links
        for (let i = 0; i < 2; i++) {
          const { fill, stroke } = nextColour();
          const link = createObject({
            id: uid('rope-link'), type: 'circle',
            x: canvasX, y: canvasY + ropeSegL * (i + 1),
            radius: 12, restitution: 0.3, friction: 0.1, density: 0.003,
            fillColor: fill, strokeColor: stroke, strokeWidth: 2.5,
          });
          vp.addChild(link.display);
          rt.physics.addBodies(link.body);
          rt.sync.register(link.id, link.body, link.display);
          ia.selection.register(link);
          store.addObject(link);
          dynRef.current.push(link.body);
          setBodyCount(dynRef.current.length);

          creg.add(createConstraint({
            type: 'rope',
            bodyA: prevBody, bodyB: link.body,
            length: ropeSegL, stiffness: 0.9,
          }));
          prevBody = link.body;
        }

        // The third (terminal) link is the receptor sensor bob
        const sensor = Matter.Bodies.circle(canvasX, canvasY + ropeSegL * 3, 6, {
          isSensor: true,
          label: `sensor-target:${constraintId}`,
          density: 0.001,
          frictionAir: 0.05,
        });
        rt.physics.addBodies(sensor);

        creg.add(createConstraint({
          id: constraintId,
          type: 'rope',
          bodyA: prevBody, bodyB: sensor,
          length: ropeSegL, stiffness: 0.9,
        }));
      }
    }
  }, [ready]);

  // Spawn a free constraint system when clicking the menu button directly
  const spawnConstraintShape = useCallback(async (type: 'pivot' | 'spring' | 'rope') => {
    const rt = runtimeRef.current;
    const ia = interactionRef.current;
    const creg = constraintRegRef.current;
    const el = mountRef.current;
    if (!rt || !ia || !creg || !el || !ready) return;

    const W = el.clientWidth || 800;
    const y = 80 + Math.random() * 40;
    const x = 120 + Math.random() * (W - 240);

    await spawnConstraintAt(type, x, y, null);
  }, [ready, spawnConstraintAt]);

  /**
   * Spawn a pendulum-rope asset at the given canvas position.
   *
   * Drops a complete, ready-to-swing pendulum arm:
   *   • A static ceiling anchor pin (the pivot)
   *   • N small rope-link circles connected by rope constraints
   *   • A glowing receptor sensor bob at the bottom that accepts any
   *     dropped circle or rectangle via checkConstraintSnapping()
   *
   * The user can then drag any Shape asset and drop it onto the
   * blinking bob to attach it as the pendulum weight.
   */
  const spawnPendulumRope = useCallback(async (
    canvasX: number,
    canvasY: number,
  ) => {
    const rt = runtimeRef.current;
    const ia = interactionRef.current;
    const creg = constraintRegRef.current;
    const store = storeRef.current;
    if (!rt || !ia || !creg || !store || !ready) return;

    const { createObject } = await import('../objects/objectFactory');
    const { createConstraint } = await import('../constraints/constraintFactory');
    const Matter = await import('matter-js');
    const vp = rt.renderer.getViewport();

    const ARM_LEN = 160; // px — pendulum arm length (pin → bob)

    // ── 1. Static ceiling anchor pin ──────────────────────────────────────
    const pin = createObject({
      id: uid('rope-pin'), type: 'circle',
      x: canvasX, y: canvasY, radius: 7,
      isStatic: true,
      fillColor: 0x1e293b, strokeColor: 0x6366f1, strokeWidth: 2.5,
    });
    vp.addChild(pin.display);
    rt.physics.addBodies(pin.body);
    rt.sync.register(pin.id, pin.body, pin.display);

    // ── 2. Terminal receptor sensor with visible drop-zone display ──────────
    const terminalId   = uid('rope-terminal');
    const sensorDispId = uid('rope-sensor-disp');

    const sensor = Matter.Bodies.circle(
      canvasX,
      canvasY + ARM_LEN,
      16,
      {
        isSensor: true,
        // Encode both IDs so checkConstraintSnapping can clean up the display
        label: `sensor-target:${terminalId}:${sensorDispId}`,
        density: 0.0005,
        frictionAir: 0.04,
      },
    );
    rt.physics.addBodies(sensor);

    creg.add(createConstraint({
      id: terminalId,
      type: 'rope',
      bodyA: pin.body,
      bodyB: sensor,
      length: ARM_LEN,
      stiffness: 1,
    }));

    // ── 4. Visible drop-zone ring that tracks the sensor via SyncRegistry ───
    const PIXI = await import('pixi.js');
    const dropZone = new PIXI.Container();

    const ring = new PIXI.Graphics();
    // Outer glow rings
    ring.lineStyle(2.5, 0x6366f1, 0.9);
    ring.drawCircle(0, 0, 20);
    ring.lineStyle(1.5, 0x818cf8, 0.35);
    ring.drawCircle(0, 0, 32);
    // Inner filled dot
    ring.beginFill(0x4f46e5, 0.35);
    ring.drawCircle(0, 0, 10);
    ring.endFill();
    // Crosshair guides
    ring.lineStyle(1, 0x818cf8, 0.6);
    ring.moveTo(-16, 0); ring.lineTo(16, 0);
    ring.moveTo(0, -16); ring.lineTo(0, 16);

    dropZone.addChild(ring);
    dropZone.x = canvasX;
    dropZone.y = canvasY + ARM_LEN;
    vp.addChild(dropZone);

    // Register so the sync loop keeps the ring over the dangling sensor each frame
    rt.sync.register(sensorDispId, sensor, dropZone);

    // Track the pin so bodyCount reflects the new system
    dynRef.current.push(pin.body);
    setBodyCount(dynRef.current.length);
  }, [ready]);


  // Spawn at a specific canvas-relative position (used by drop handler)
  const spawnAt = useCallback(async (
    type: 'circle' | 'rectangle',
    canvasX: number,
    canvasY: number,
  ) => {
    const rt = runtimeRef.current;
    const ia = interactionRef.current;
    const store = storeRef.current;
    if (!rt || !ia || !store || !ready) return;

    const { createObject } = await import('../objects/objectFactory');
    const size = 32 + Math.random() * 24;
    const { fill, stroke } = nextColour();
    const base = {
      x: canvasX, y: canvasY, restitution: 0.6, friction: 0.1,
      density: 0.002, fillColor: fill, strokeColor: stroke, strokeWidth: 2.5
    };

    const obj = type === 'circle'
      ? createObject({ id: uid('circle'), type: 'circle', radius: size / 2, ...base })
      : createObject({
        id: uid('rect'), type: 'rectangle', width: size, height: size,
        cornerRadius: 8, ...base
      });

    rt.renderer.getViewport().addChild(obj.display);
    rt.physics.addBodies(obj.body);
    rt.sync.register(obj.id, obj.body, obj.display);
    ia.selection.register(obj);
    store.addObject(obj);
    dynRef.current.push(obj.body);
    setBodyCount(dynRef.current.length);
    checkConstraintSnapping(obj.body);
  }, [ready, checkConstraintSnapping]);

  const onPanelPointerDown = (type: PanelDragType) =>
    (e: React.PointerEvent) => {
      if (!ready) return;
      e.currentTarget.setPointerCapture(e.pointerId);

      // Pause physics engine drag controller during menu drag-and-drop to prevent automatic sticking
      interactionRef.current?.drag.disable();

      panelDragRef.current = type;
      didDragRef.current = false;   // reset flag on every fresh press
      setIsDragging(true);
      setGhostPos({ x: e.clientX, y: e.clientY });
    };

  const onPanelPointerMove = (e: React.PointerEvent) => {
    if (!isDragging) return;
    didDragRef.current = true;    // pointer moved — this is a drag, not a tap
    setGhostPos({ x: e.clientX, y: e.clientY });

    const canvas = mountRef.current;
    if (canvas) {
      const r = canvas.getBoundingClientRect();
      const over = (
        e.clientX >= r.left && e.clientX <= r.right &&
        e.clientY >= r.top && e.clientY <= r.bottom
      );
      setIsOverCanvas(over);

      // Query body under cursor for constraints
      const dragType = panelDragRef.current;
      if (over && dragType && ['pivot', 'spring', 'rope'].includes(dragType)) {
        const canvasX = e.clientX - r.left;
        const canvasY = e.clientY - r.top;
        const queryPoint = { x: canvasX, y: canvasY };
        const bodies = dynRef.current;

        import('matter-js').then((Matter) => {
          const hovered = bodies.find(b => Matter.Vertices.contains(b.vertices, queryPoint));
          if (hovered) {
            hoveredBodyRef.current = hovered;
            setHoveredBodyId(hovered.label || hovered.id.toString());
          } else {
            hoveredBodyRef.current = null;
            setHoveredBodyId(null);
          }
        });
      } else {
        hoveredBodyRef.current = null;
        setHoveredBodyId(null);
      }
    }
  };

  const onPanelPointerUp = (e: React.PointerEvent) => {
    if (!isDragging) return;
    const type = panelDragRef.current;
    panelDragRef.current = null;
    setIsDragging(false);
    setIsOverCanvas(false);

    // Re-enable the physics engine drag controller now that panel drag is complete
    interactionRef.current?.drag.enable();

    const hoveredBody = hoveredBodyRef.current;
    hoveredBodyRef.current = null;
    setHoveredBodyId(null);

    if (!type) return;
    const canvas = mountRef.current;
    if (!canvas) return;
    const r = canvas.getBoundingClientRect();
    // Only drop if released over the canvas
    if (e.clientX >= r.left && e.clientX <= r.right &&
      e.clientY >= r.top && e.clientY <= r.bottom) {
      const canvasX = e.clientX - r.left;
      const canvasY = e.clientY - r.top;
      if (['pivot', 'spring', 'rope'].includes(type)) {
        spawnConstraintAt(type as 'pivot' | 'spring' | 'rope', canvasX, canvasY, hoveredBody);
      } else if (type === 'pendulum-rope') {
        spawnPendulumRope(canvasX, canvasY);
      } else {
        spawnAt(type as 'circle' | 'rectangle', canvasX, canvasY);
      }
    }
  };

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div style={S.root}>
      {/* ── Left panel ─────────────────────────────────────── */}
      <aside style={S.panel}>
        <div style={S.header}>
          <span style={S.pulse} />
          <span style={S.tag}>Interactive Physics</span>
        </div>
        <h1 style={S.title}>EduSim Sandbox</h1>
        <p style={S.subtitle}>Drag · Select · Control</p>

        {/* Status */}
        <div style={S.cards}>
          <div style={S.card}>
            <div style={S.cardLbl}>Engine</div>
            <div style={S.cardVal}>
              <span style={{ ...S.dot, background: running ? '#10b981' : '#f59e0b' }} />
              {ready ? (running ? 'Running' : 'Paused') : 'Loading…'}
            </div>
          </div>
          <div style={S.card}>
            <div style={S.cardLbl}>Dynamic Bodies</div>
            <div style={S.cardVal}>{bodyCount}</div>
          </div>
        </div>



        <Sep label="Controls" />
        <div style={S.row}>
          <button style={{ ...S.btn, ...S.btnPrimary, flex: 1 }} onClick={togglePlay} disabled={!ready}>
            {running ? '⏸ Pause' : '▶ Resume'}
          </button>
          <button style={{ ...S.btn, ...S.btnGhost }} onClick={handleReset} disabled={!ready} title="Reset">↺</button>
        </div>

        <Sep label="Spawn Shapes — click or drag" />
        <div
          style={S.row}
          onPointerMove={onPanelPointerMove}
          onPointerUp={onPanelPointerUp}
        >
          <button
            style={{ ...S.btn, ...S.btnIndigo, flex: 1, cursor: ready ? 'grab' : 'not-allowed' }}
            disabled={!ready}
            onClick={() => { if (didDragRef.current) { didDragRef.current = false; return; } spawnShape('rectangle'); }}
            onPointerDown={onPanelPointerDown('rectangle')}
          >▪ Rectangle</button>
          <button
            style={{ ...S.btn, ...S.btnEmerald, flex: 1, cursor: ready ? 'grab' : 'not-allowed' }}
            disabled={!ready}
            onClick={() => { if (didDragRef.current) { didDragRef.current = false; return; } spawnShape('circle'); }}
            onPointerDown={onPanelPointerDown('circle')}
          >● Circle</button>
        </div>
        {/* Rope as a first-class shape asset */}
        <div
          style={{ ...S.row, marginTop: -2 }}
          onPointerMove={onPanelPointerMove}
          onPointerUp={onPanelPointerUp}
        >
          <button
            style={{
              ...S.btn,
              width: '100%',
              cursor: ready ? 'grab' : 'not-allowed',
              background: 'rgba(99,102,241,0.13)',
              color: '#a5b4fc',
              borderColor: 'rgba(99,102,241,0.28)',
              display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
            }}
            disabled={!ready}
            onClick={() => {
              if (didDragRef.current) { didDragRef.current = false; return; }
              const el = mountRef.current;
              if (!el) return;
              const W = el.clientWidth || 800;
              spawnPendulumRope(120 + Math.random() * (W - 240), 40 + Math.random() * 30);
            }}
            onPointerDown={onPanelPointerDown('pendulum-rope')}
          >
            <span style={{ fontSize: 13 }}>🪢</span>
            <span>Rope  <span style={{ fontSize: 9, opacity: 0.65 }}>— drop bob to complete pendulum</span></span>
          </button>
        </div>

        <Sep label="Spawn Constraints — click or drag" />
        <div
          style={{ ...S.row, flexWrap: 'wrap' }}
          onPointerMove={onPanelPointerMove}
          onPointerUp={onPanelPointerUp}
        >
          <button
            style={{ ...S.btn, ...S.btnIndigo, flex: '1 1 45%', cursor: ready ? 'grab' : 'not-allowed', padding: '7px 4px', fontSize: 11 }}
            disabled={!ready}
            onClick={() => { if (didDragRef.current) { didDragRef.current = false; return; } spawnConstraintShape('pivot'); }}
            onPointerDown={onPanelPointerDown('pivot')}
          >📌 Pivot</button>
          <button
            style={{ ...S.btn, ...S.btnEmerald, flex: '1 1 45%', cursor: ready ? 'grab' : 'not-allowed', padding: '7px 4px', fontSize: 11 }}
            disabled={!ready}
            onClick={() => { if (didDragRef.current) { didDragRef.current = false; return; } spawnConstraintShape('spring'); }}
            onPointerDown={onPanelPointerDown('spring')}
          >🌀 Spring</button>
          <button
            style={{ ...S.btn, ...S.btnSky, width: '100%', cursor: ready ? 'grab' : 'not-allowed', marginTop: 4 }}
            disabled={!ready}
            onClick={() => { if (didDragRef.current) { didDragRef.current = false; return; } spawnConstraintShape('rope'); }}
            onPointerDown={onPanelPointerDown('rope')}
          >🔗 Rope Chain</button>
        </div>

        <Sep label="Impulse" />
        <button style={{ ...S.btn, ...S.btnSky, width: '100%', marginBottom: 8 }} onClick={blast} disabled={!ready}>↑ Upward Blast</button>
        <div style={S.row}>
          <button style={{ ...S.btn, ...S.btnGhost, flex: 1 }} onClick={() => push('left')} disabled={!ready}>◀ Left</button>
          <button style={{ ...S.btn, ...S.btnGhost, flex: 1 }} onClick={() => push('right')} disabled={!ready}>Right ▶</button>
        </div>

        <Sep label="Gravity" />
        <div style={S.gravRow}>
          {(Object.keys(GRAVITY_VALUES) as GravityPreset[]).map((k) => (
            <button key={k}
              style={{ ...S.gravBtn, ...(gravity === k ? S.gravActive : {}) }}
              onClick={() => changeGravity(k)} disabled={!ready}
            >{k}</button>
          ))}
        </div>

        <Sep label="Simulation Speed" />
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
          <input
            type="range" min={0.1} max={3} step={0.1}
            value={speed} disabled={!ready}
            onChange={(e) => changeSpeed(parseFloat(e.target.value))}
            style={{ flex: 1, accentColor: '#6366f1' }}
          />
          <span style={{ fontSize: 11, color: '#818cf8', minWidth: 30, textAlign: 'right' }}>{speed.toFixed(1)}×</span>
        </div>

        <Sep label="Constraint Tuning" />
        {storeRef.current && storeRef.current.getAllConstraints().length > 0 ? (
          <div style={S.constraintsList}>
            {storeRef.current.getAllConstraints().map((rc) => {
              const { id, type, constraint } = rc;
              const hasStiffness = type === 'spring' || type === 'pivot' || type === 'rope';
              const hasDamping = type === 'spring' || type === 'pivot';
              const hasLength = true;

              return (
                <div key={id} style={S.constraintCard}>
                  <div style={S.constraintCardHeader}>
                    <span style={S.constraintName}>
                      {type === 'spring' ? '🌀 Spring' : type === 'pivot' ? '📌 Pivot' : '🔗 Rope Link'}
                    </span>
                    <span style={{ fontSize: 9, color: '#475569', fontFamily: 'monospace' }}>{id}</span>
                  </div>

                  {hasStiffness && (
                    <div style={S.controlRow}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <label style={S.controlLabel}>Stiffness</label>
                        <span style={S.controlVal}>{constraint.stiffness.toFixed(3)}</span>
                      </div>
                      <div style={S.sliderContainer}>
                        <input
                          type="range"
                          min={type === 'spring' ? 0.001 : 0.05}
                          max={1.0}
                          step={type === 'spring' ? 0.002 : 0.05}
                          value={constraint.stiffness}
                          onChange={(e) => propertyControllerRef.current?.updateConstraintProperty(id, 'stiffness', parseFloat(e.target.value))}
                          style={S.slider}
                        />
                      </div>
                    </div>
                  )}

                  {hasDamping && (
                    <div style={S.controlRow}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <label style={S.controlLabel}>Damping</label>
                        <span style={S.controlVal}>{constraint.damping.toFixed(4)}</span>
                      </div>
                      <div style={S.sliderContainer}>
                        <input
                          type="range"
                          min={0.0}
                          max={0.1}
                          step={0.002}
                          value={constraint.damping}
                          onChange={(e) => propertyControllerRef.current?.updateConstraintProperty(id, 'damping', parseFloat(e.target.value))}
                          style={S.slider}
                        />
                      </div>
                    </div>
                  )}

                  {hasLength && (
                    <div style={S.controlRow}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <label style={S.controlLabel}>Rest Length</label>
                        <span style={S.controlVal}>{Math.round(constraint.length)} px</span>
                      </div>
                      <div style={S.sliderContainer}>
                        <input
                          type="range"
                          min={10}
                          max={350}
                          step={5}
                          value={constraint.length}
                          onChange={(e) => propertyControllerRef.current?.updateConstraintProperty(id, 'length', parseFloat(e.target.value))}
                          style={S.slider}
                        />
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <div style={S.noSelectionCard}>
            <span style={{ color: '#475569', fontSize: 10 }}>No active constraints to tune.</span>
          </div>
        )}

        <p style={S.hint}>
          <strong style={{ color: '#6366f1' }}>Drag</strong> objects · <strong style={{ color: '#6366f1' }}>Click</strong> to select · Use controls to shape the simulation.
        </p>
      </aside>

      {/* ── Canvas ─────────────────────────────────────────── */}
      <div
        style={{
          ...S.canvasWrap,
          outline: isOverCanvas ? '2px dashed rgba(99,102,241,0.6)' : 'none',
          outlineOffset: '-3px',
        }}
        onClick={() => interactionRef.current?.selection.deselect()}
        onPointerMove={onPanelPointerMove}
        onPointerUp={onPanelPointerUp}
      >
        <div style={S.dotGrid} />
        <div ref={mountRef} style={S.mount} />

        {/* Drop hint overlay */}
        {isOverCanvas && (
          <div style={S.dropHint}>
            {hoveredBodyId ? (
              <span>Connect <span style={{ color: '#818cf8', fontWeight: 'bold' }}>{panelDragRef.current}</span> to <span style={{ color: '#fb7185', fontWeight: 'bold' }}>{hoveredBodyId}</span></span>
            ) : (
              <span>Release to drop <span style={{ color: '#a5b4fc', fontWeight: 'bold' }}>new {panelDragRef.current}</span></span>
            )}
          </div>
        )}

        <div style={S.badge}>
          <span style={{ ...S.dot, background: '#6366f1', marginRight: 6 }} />
          Drag shapes & constraints · Drop anywhere
        </div>


        {/* Floating glassmorphic STEM Laboratory HUD Overlay */}
        {selected && (
          <div style={S.floatingHud}>
            <div style={S.floatingHudTitle}>🔬 F = ma Educational HUD</div>
            <div ref={hudFormulaRef} style={S.floatingHudEq}>
              <div style={{ fontSize: 15, fontWeight: 800, color: '#fde047', textShadow: '0 0 10px rgba(253,224,71,0.25)' }}>
                F = m &middot; a
              </div>
              <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 4, fontFamily: 'monospace' }}>
                0.0 N = 10.0 kg &times; 0.00 m/s&sup2;
              </div>
            </div>
            <div style={S.floatingHudGrid}>
              <div style={S.floatingHudCard}>
                <span style={S.floatingHudLabel}>Applied Force</span>
                <span ref={hudForceRef} style={{ ...S.floatingHudValue, color: '#ef4444' }}>0.0 N</span>
              </div>
              <div style={S.floatingHudCard}>
                <span style={S.floatingHudLabel}>Mass</span>
                <span ref={hudMassRef} style={{ ...S.floatingHudValue, color: '#c084fc' }}>10.0 kg</span>
              </div>
              <div style={S.floatingHudCard}>
                <span style={S.floatingHudLabel}>Applied Accel.</span>
                <span ref={hudAccRef} style={{ ...S.floatingHudValue, color: '#10b981' }}>0.00 m/s²</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ── Right panel ─────────────────────────────────────── */}
      <aside style={S.rightSidebar}>
        {propertyControllerRef.current && storeRef.current && (
          <PropertyPanel
            store={storeRef.current}
            propertyController={propertyControllerRef.current}
            observableEngine={observableEngineRef.current}
          />
        )}
      </aside>

      {/* ── Drag ghost (follows cursor globally) ──────────── */}
      {isDragging && (
        <div
          style={{
            position: 'fixed',
            left: ghostPos.x,
            top: ghostPos.y,
            transform: 'translate(-50%, -50%)',
            width:  ['pivot', 'spring', 'rope'].includes(panelDragRef.current || '') ? 48
                  : panelDragRef.current === 'pendulum-rope' ? 52
                  : (panelDragRef.current === 'circle' ? 44 : 40),
            height: ['pivot', 'spring', 'rope'].includes(panelDragRef.current || '') ? 48
                  : panelDragRef.current === 'pendulum-rope' ? 52
                  : (panelDragRef.current === 'circle' ? 44 : 40),
            borderRadius: panelDragRef.current === 'circle' || panelDragRef.current === 'pivot' ? '50%'
                        : panelDragRef.current === 'pendulum-rope' ? 12
                        : 10,
            background: panelDragRef.current === 'circle'
              ? 'rgba(16,185,129,0.55)'
              : panelDragRef.current === 'rectangle'
                ? 'rgba(99,102,241,0.55)'
                : panelDragRef.current === 'pendulum-rope'
                  ? 'rgba(99,102,241,0.45)'
                  : panelDragRef.current === 'pivot'
                    ? 'rgba(139,92,246,0.55)'
                    : panelDragRef.current === 'spring'
                      ? 'rgba(16,185,129,0.55)'
                      : 'rgba(251,191,36,0.55)',
            border: `2px solid ${
              panelDragRef.current === 'pendulum-rope' ? '#818cf8' :
              panelDragRef.current === 'circle' || panelDragRef.current === 'spring' ? '#6ee7b7' :
              panelDragRef.current === 'rectangle' ? '#a5b4fc' :
              panelDragRef.current === 'pivot' ? '#c084fc' : '#fde047'
            }`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 18,
            color: '#fff',
            backdropFilter: 'blur(6px)',
            pointerEvents: 'none',
            zIndex: 9999,
            transition: 'opacity 0.1s',
            boxShadow: isOverCanvas
              ? '0 0 0 6px rgba(99,102,241,0.25), 0 8px 24px rgba(0,0,0,0.4)'
              : '0 4px 16px rgba(0,0,0,0.35)',
          }}
        >
          {panelDragRef.current === 'pivot' && '📌'}
          {panelDragRef.current === 'spring' && '🌀'}
          {panelDragRef.current === 'rope' && '🔗'}
          {panelDragRef.current === 'pendulum-rope' && '🪢'}
        </div>
      )}

    </div>
  );
};

// ─── Helpers ──────────────────────────────────────────────────────────────────

const Sep: React.FC<{ label: string }> = ({ label }) => (
  <div style={{
    margin: '14px 0 10px', fontSize: 9, fontWeight: 700,
    letterSpacing: '0.12em', color: '#334155', textTransform: 'uppercase' as const,
    borderBottom: '1px solid #1e293b', paddingBottom: 4
  }}>{label}</div>
);

// ─── Styles ───────────────────────────────────────────────────────────────────

const S: Record<string, React.CSSProperties> = {
  root: {
    display: 'flex', width: '100%', height: '100%', minHeight: 560,
    background: '#dbeafe', color: '#0f172a',
    fontFamily: '"Plus Jakarta Sans",system-ui,sans-serif',
    overflow: 'hidden', userSelect: 'none'
  },
  panel: {
    width: 288, minWidth: 268, height: '100%', padding: '20px 16px',
    background: 'rgba(15,23,42,0.92)', backdropFilter: 'blur(20px)',
    borderRight: '1px solid rgba(255,255,255,0.06)',
    display: 'flex', flexDirection: 'column', overflowY: 'auto'
  },
  rightSidebar: {
    width: 320, minWidth: 300, height: '100%', background: 'rgba(15,23,42,0.92)',
    backdropFilter: 'blur(20px)', borderLeft: '1px solid rgba(255,255,255,0.06)',
    display: 'flex', flexDirection: 'column', overflowY: 'auto'
  },
  header: { display: 'flex', alignItems: 'center', gap: 7, marginBottom: 4 },
  pulse: {
    width: 9, height: 9, borderRadius: '50%', background: '#6366f1',
    boxShadow: '0 0 0 3px rgba(99,102,241,0.28)', flexShrink: 0
  },
  tag: {
    fontSize: 10, fontWeight: 700, letterSpacing: '0.12em',
    color: '#818cf8', textTransform: 'uppercase'
  },
  title: {
    fontSize: 22, fontWeight: 800, margin: '2px 0 2px', letterSpacing: '-0.03em',
    background: 'linear-gradient(135deg,#c7d2fe,#bfdbfe)',
    WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent'
  },
  subtitle: { fontSize: 11, color: '#475569', marginBottom: 16 },
  cards: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 8 },
  card: {
    background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.07)',
    borderRadius: 10, padding: '9px 11px', transition: 'border-color 0.2s'
  },
  cardLbl: {
    fontSize: 9, fontWeight: 700, letterSpacing: '0.1em',
    color: '#64748b', textTransform: 'uppercase', marginBottom: 4
  },
  cardVal: {
    fontSize: 13, fontWeight: 600, color: '#cbd5e1',
    display: 'flex', alignItems: 'center', gap: 5
  },
  dot: { display: 'inline-block', width: 7, height: 7, borderRadius: '50%', flexShrink: 0 },
  row: { display: 'flex', gap: 8, marginBottom: 8 },
  btn: {
    padding: '7px 12px', borderRadius: 8, border: '1px solid transparent',
    cursor: 'pointer', fontSize: 12, fontWeight: 600,
    transition: 'opacity 0.15s', outline: 'none'
  },
  btnPrimary: { background: '#4f46e5', color: '#fff', borderColor: '#4338ca' },
  btnGhost: { background: 'rgba(255,255,255,0.06)', color: '#94a3b8', borderColor: 'rgba(255,255,255,0.1)' },
  btnIndigo: { background: 'rgba(99,102,241,0.18)', color: '#a5b4fc', borderColor: 'rgba(99,102,241,0.3)' },
  btnEmerald: { background: 'rgba(16,185,129,0.18)', color: '#6ee7b7', borderColor: 'rgba(16,185,129,0.3)' },
  btnSky: { background: 'rgba(14,165,233,0.18)', color: '#7dd3fc', borderColor: 'rgba(14,165,233,0.3)' },
  gravRow: {
    display: 'flex', gap: 4, background: 'rgba(0,0,0,0.35)',
    borderRadius: 10, padding: 4, border: '1px solid rgba(255,255,255,0.06)', marginBottom: 16
  },
  gravBtn: {
    flex: 1, padding: '5px 0', background: 'transparent', border: 'none',
    borderRadius: 7, cursor: 'pointer', fontSize: 10, fontWeight: 700,
    color: '#475569', textTransform: 'uppercase', letterSpacing: '0.06em', transition: 'all 0.15s'
  },
  gravActive: { background: '#4f46e5', color: '#fff' },
  hint: {
    fontSize: 10, color: '#334155', lineHeight: 1.55, marginTop: 'auto', paddingTop: 14,
    borderTop: '1px solid rgba(255,255,255,0.04)'
  },
  canvasWrap: { flex: 1, position: 'relative', overflow: 'hidden', background: '#bfdbfe', cursor: 'default', transition: 'outline 0.15s' },
  dropHint: {
    position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%,-50%)',
    padding: '8px 18px', borderRadius: 10, background: 'rgba(99,102,241,0.2)',
    border: '1px solid rgba(99,102,241,0.4)', color: '#a5b4fc', fontSize: 13,
    fontWeight: 600, pointerEvents: 'none', backdropFilter: 'blur(8px)'
  },
  dotGrid: {
    position: 'absolute', inset: 0, pointerEvents: 'none',
    backgroundImage: 'radial-gradient(#1e293b 1px,transparent 1px)',
    backgroundSize: '18px 18px', opacity: 0.55
  },
  mount: { position: 'absolute', inset: 0 },
  badge: {
    position: 'absolute', bottom: 14, right: 14, display: 'flex', alignItems: 'center',
    padding: '5px 12px', borderRadius: 8, backdropFilter: 'blur(12px)',
    background: 'rgba(15,23,42,0.8)', border: '1px solid rgba(255,255,255,0.08)',
    fontSize: 11, color: '#818cf8', pointerEvents: 'none'
  },

  // Property Editor Panel Styles
  editorContainer: {
    background: 'rgba(255, 255, 255, 0.02)',
    border: '1px solid rgba(255, 255, 255, 0.06)',
    borderRadius: 12,
    padding: '10px 12px',
    marginBottom: 8,
    display: 'flex',
    flexDirection: 'column',
    gap: 10,
  },
  editorHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
    paddingBottom: 4,
  },
  editorTitle: {
    fontSize: 12,
    fontWeight: 700,
    color: '#a5b4fc',
  },
  deselectBtn: {
    background: 'transparent',
    border: 'none',
    color: '#64748b',
    cursor: 'pointer',
    fontSize: 12,
    padding: 0,
    lineHeight: '1',
  },
  editorSection: {
    display: 'flex',
    flexDirection: 'column',
    gap: 6,
  },
  sectionLabel: {
    fontSize: 8,
    fontWeight: 700,
    color: '#64748b',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.08em',
  },
  controlRow: {
    display: 'flex',
    flexDirection: 'column',
    gap: 3,
  },
  toggleRow: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 2,
  },
  toggleBtn: {
    padding: '4px 8px',
    borderRadius: 6,
    border: '1px solid',
    cursor: 'pointer',
    fontSize: 9,
    fontWeight: 600,
    transition: 'all 0.15s',
  },
  controlLabel: {
    fontSize: 9,
    color: '#94a3b8',
  },
  sliderContainer: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
  },
  slider: {
    flex: 1,
    accentColor: '#6366f1',
    cursor: 'pointer',
    height: 4,
  },
  controlVal: {
    fontSize: 9,
    color: '#818cf8',
    minWidth: 32,
    textAlign: 'right' as const,
    fontFamily: 'monospace',
  },
  colorPalette: {
    display: 'flex',
    gap: 4,
    flexWrap: 'wrap',
    marginTop: 2,
  },
  telemetryGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: 4,
    background: 'rgba(0, 0, 0, 0.25)',
    borderRadius: 8,
    padding: 6,
    border: '1px solid rgba(255, 255, 255, 0.03)',
  },
  telemetryItem: {
    display: 'flex',
    flexDirection: 'column',
  },
  telemetryLabel: {
    fontSize: 7,
    color: '#475569',
    textTransform: 'uppercase' as const,
  },
  telemetryVal: {
    fontSize: 9,
    color: '#94a3b8',
    fontFamily: 'monospace',
  },
  noSelectionCard: {
    padding: '10px',
    borderRadius: 8,
    border: '1px dashed rgba(255, 255, 255, 0.08)',
    textAlign: 'center' as const,
    background: 'rgba(255, 255, 255, 0.01)',
  },
  constraintsList: {
    display: 'flex',
    flexDirection: 'column',
    gap: 8,
    maxHeight: 180,
    overflowY: 'auto' as const,
    paddingRight: 4,
    marginBottom: 8,
  },
  constraintCard: {
    background: 'rgba(255, 255, 255, 0.02)',
    border: '1px solid rgba(255, 255, 255, 0.05)',
    borderRadius: 8,
    padding: 6,
    display: 'flex',
    flexDirection: 'column',
    gap: 4,
  },
  constraintCardHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderBottom: '1px solid rgba(255, 255, 255, 0.03)',
    paddingBottom: 2,
  },
  constraintName: {
    fontSize: 9,
    fontWeight: 600,
    color: '#cbd5e1',
  },
  floatingHud: {
    position: 'absolute',
    top: 14,
    right: 14,
    width: 260,
    background: 'rgba(15, 23, 42, 0.88)',
    backdropFilter: 'blur(20px)',
    border: '1px solid rgba(255, 255, 255, 0.08)',
    borderRadius: 12,
    padding: 12,
    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4), inset 0 1px 1px rgba(255, 255, 255, 0.05)',
    display: 'flex',
    flexDirection: 'column',
    gap: 8,
    pointerEvents: 'none',
    zIndex: 100,
  },
  floatingHudTitle: {
    fontSize: 9,
    fontWeight: 800,
    color: '#818cf8',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.08em',
    borderBottom: '1px solid rgba(255, 255, 255, 0.04)',
    paddingBottom: 4,
  },
  floatingHudEq: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'rgba(0, 0, 0, 0.3)',
    borderRadius: 8,
    padding: '8px 10px',
    textAlign: 'center' as const,
  },
  floatingHudGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr 1.2fr',
    gap: 6,
  },
  floatingHudCard: {
    display: 'flex',
    flexDirection: 'column',
    background: 'rgba(255, 255, 255, 0.02)',
    border: '1px solid rgba(255, 255, 255, 0.04)',
    borderRadius: 6,
    padding: '5px 6px',
    textAlign: 'center' as const,
  },
  floatingHudLabel: {
    fontSize: 7,
    color: '#64748b',
    fontWeight: 700,
    textTransform: 'uppercase' as const,
    marginBottom: 2,
  },
  floatingHudValue: {
    fontSize: 9,
    fontWeight: 700,
    fontFamily: 'monospace',
  },
};

export default SandboxCanvas;
