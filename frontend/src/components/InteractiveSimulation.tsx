import React, { useEffect, useRef, useState } from 'react';
import Matter from 'matter-js';
import { Play, Pause, RotateCcw, Sliders, Cpu, Activity } from 'lucide-react';
import { motion } from 'framer-motion';
import { SimulationDSL, SimulationObject, FormulaBinding } from '../services/api';

interface InteractiveSimulationProps {
  dsl: SimulationDSL;
  prompt: string;
}

export const InteractiveSimulation: React.FC<InteractiveSimulationProps> = ({ dsl, prompt }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);
  
  // Matter.js instances
  const engineRef = useRef<Matter.Engine | null>(null);
  const runnerRef = useRef<Matter.Runner | null>(null);
  const bodyRefs = useRef<Record<number, Matter.Body>>({});
  const bodyMapRef = useRef<Record<string, Matter.Body>>({});
  const mouseConstraintRef = useRef<Matter.MouseConstraint | null>(null);
  
  // Simulation playback state
  const [isPaused, setIsPaused] = useState(false);
  const [scaleFactor, setScaleFactor] = useState({ x: 50, y: 50 });
  const [paramValues, setParamValues] = useState<Record<string, number>>({});
  
  // State for real-time telemetry variables (forces solver updates)
  const [, setTelemetryTick] = useState(0);
  const [activeConstraints, setActiveConstraints] = useState<{
    id: string;
    constraint: Matter.Constraint;
    color: string;
    lineWidth: number;
  }[]>([]);

  const canvasWidth = 1000;
  const canvasHeight = 600;

  // 1. Initial State / Setup parameter slider defaults
  useEffect(() => {
    const initialParams: Record<string, number> = {};
    
    // Sliders
    dsl.controls.parameters.forEach((param) => {
      if (param.type === 'slider') {
        const bind = param.bind;
        let defaultVal = (param.min! + param.max!) / 2;
        
        // Match initial values from DSL if possible
        if (bind === 'environment.gravity.y') {
          defaultVal = dsl.environment.gravity.y;
        } else if (bind === 'environment.gravity.x') {
          defaultVal = dsl.environment.gravity.x;
        } else {
          const match = bind.match(/^objects\[(\d+)\]\.physics\.mass$/);
          if (match) {
            const idx = parseInt(match[1]);
            defaultVal = dsl.objects[idx]?.physics.mass || 1;
          }
        }
        initialParams[param.id] = defaultVal;
      } else if (param.type === 'toggle') {
        initialParams[param.id] = 1; // On
      }
    });

    setParamValues(initialParams);
  }, [dsl]);

  // 2. Initialize Physics Engine
  useEffect(() => {
    // Create Matter.js engine
    const engine = Matter.Engine.create({
      gravity: {
        x: dsl.environment.gravity.x,
        y: dsl.environment.gravity.y,
        scale: 0.001 // Normal scale
      }
    });
    engineRef.current = engine;

    const runner = Matter.Runner.create();
    runnerRef.current = runner;
    Matter.Runner.run(runner, engine);

    // Calculate coordinate scaling multipliers based on DSL world configuration
    const worldWidth = (dsl.environment as any).world?.width || 20;
    const worldHeight = (dsl.environment as any).world?.height || 12;
    const multX = canvasWidth / worldWidth;
    const multY = canvasHeight / worldHeight;
    setScaleFactor({ x: multX, y: multY });

    bodyRefs.current = {};
    bodyMapRef.current = {};

    // Create Ground boundary if enabled
    if ((dsl.environment as any).boundaries?.enabled !== false) {
      const ground = Matter.Bodies.rectangle(
        canvasWidth / 2,
        canvasHeight - 15,
        canvasWidth,
        30,
        { isStatic: true, friction: 0.8, restitution: 0.1 }
      );
      Matter.World.add(engine.world, ground);
    }

    // Add objects from DSL
    dsl.objects.forEach((obj, idx) => {
      const px = obj.position.x * multX;
      const py = obj.position.y * multY;
      const isStatic = obj.bodyType === 'static';
      const mass = obj.physics.mass || 1.0;
      const restitution = obj.material.restitution ?? 0.5;
      const friction = obj.material.friction ?? 0.5;

      let body: Matter.Body;

      if (obj.shape.type === 'circle') {
        const radius = (obj.shape.radius || 1) * multX;
        body = Matter.Bodies.circle(px, py, radius, {
          isStatic,
          mass: isStatic ? 0.1 : mass, // Matter.js static mass is Infinite automatically
          restitution,
          friction
        });
      } else {
        const w = (obj.shape.width || 2) * multX;
        const h = (obj.shape.height || 2) * multY;
        body = Matter.Bodies.rectangle(px, py, w, h, {
          isStatic,
          mass: isStatic ? 0.1 : mass,
          restitution,
          friction
        });
      }

      // Scale and apply initial velocity
      if (obj.velocity) {
        Matter.Body.setVelocity(body, {
          x: obj.velocity.x * (multX / 10),
          y: obj.velocity.y * (multY / 10)
        });
      }

      // Add to Matter world
      Matter.World.add(engine.world, body);
      bodyRefs.current[idx] = body;
      bodyMapRef.current[obj.id] = body;
    });

    // Setup counter-gravity force for objects where affectedByGravity is false
    Matter.Events.on(engine, 'beforeUpdate', () => {
      const gravityY = engine.gravity.y * engine.gravity.scale;
      const gravityX = engine.gravity.x * engine.gravity.scale;
      
      dsl.objects.forEach((obj) => {
        const body = bodyMapRef.current[obj.id];
        if (body && !body.isStatic && obj.physics?.affectedByGravity === false) {
          // Apply an equal and opposite force to cancel gravity for this specific body
          Matter.Body.applyForce(body, body.position, {
            x: -gravityX * body.mass,
            y: -gravityY * body.mass
          });
        }
      });
    });

    const constraintsList: {
      id: string;
      constraint: Matter.Constraint;
      color: string;
      lineWidth: number;
    }[] = [];

    // Add dynamic constraints from DSL
    const dslConstraints = (dsl as any).constraints || [];
    dslConstraints.forEach((constDef: any) => {
      const bodyA = bodyMapRef.current[constDef.bodyA];
      const bodyB = bodyMapRef.current[constDef.bodyB];
      
      if (bodyB) {
        const constraintOptions: Matter.IConstraintDefinition = {
          bodyB: bodyB,
          stiffness: constDef.stiffness ?? 0.9,
          length: (constDef.length ?? 5) * multX,
        };
        
        if (bodyA) {
          constraintOptions.bodyA = bodyA;
        } else if (constDef.pointA) {
          constraintOptions.pointA = {
            x: constDef.pointA.x * multX,
            y: constDef.pointA.y * multY
          };
        } else {
          constraintOptions.pointA = {
            x: bodyB.position.x,
            y: bodyB.position.y - (constDef.length ?? 5) * multX
          };
        }
        
        if (constDef.pointB) {
          constraintOptions.pointB = {
            x: constDef.pointB.x * multX,
            y: constDef.pointB.y * multY
          };
        }
        
        const constraint = Matter.Constraint.create(constraintOptions);
        Matter.World.add(engine.world, constraint);
        
        constraintsList.push({
          id: constDef.id,
          constraint,
          color: constDef.visual?.color || '#cbd5e1',
          lineWidth: constDef.visual?.lineWidth || 2
        });
      }
    });

    // Fallback static pendulum constraints if no explicit constraints array exists but is pendulum/harmonic
    if (constraintsList.length === 0 && dsl.formulaBindings.some(b => b.id.includes("pendulum") || b.id.includes("constraint"))) {
      const objBody = bodyMapRef.current[dsl.objects[0]?.id] || bodyRefs.current[0];
      if (objBody) {
        const constraint = Matter.Constraint.create({
          pointA: { x: canvasWidth / 2, y: 100 },
          bodyB: objBody,
          stiffness: 0.9,
          length: 250
        });
        Matter.World.add(engine.world, constraint);
        constraintsList.push({
          id: 'fallback_pendulum',
          constraint,
          color: '#00eeff',
          lineWidth: 3.5
        });
      }
    }

    setActiveConstraints(constraintsList);

    // Add Mouse Drag Constraints
    if (containerRef.current) {
      // We overlay an invisible canvas to handle Mouse Constraints, or map directly on SVG container
      const mouse = Matter.Mouse.create(containerRef.current);
      const mouseConstraint = Matter.MouseConstraint.create(engine, {
        mouse: mouse,
        constraint: {
          stiffness: 0.1,
          render: { visible: false }
        }
      });
      Matter.World.add(engine.world, mouseConstraint);
      mouseConstraintRef.current = mouseConstraint;
    }

    // Sync Loop: sync visual transformations in real-time
    let animationId: number;
    const syncVisuals = () => {
      dsl.objects.forEach((obj) => {
        const body = bodyMapRef.current[obj.id];
        const svgElement = svgRef.current?.querySelector(`#phys_${obj.id}`);
        
        if (body && svgElement) {
          // Compute deltas from starting coordinates
          const startX = obj.position.x * multX;
          const startY = obj.position.y * multY;
          
          const dx = body.position.x - startX;
          const dy = body.position.y - startY;
          const angle = body.angle * (180 / Math.PI); // rad to deg
          
          svgElement.setAttribute(
            'transform',
            `translate(${dx}, ${dy}) rotate(${angle}, ${startX}, ${startY})`
          );
        }
      });

      // Periodic trigger for telemetry values
      setTelemetryTick(prev => prev + 1);

      animationId = requestAnimationFrame(syncVisuals);
    };

    syncVisuals();

    // Clean up
    return () => {
      cancelAnimationFrame(animationId);
      if (engineRef.current) {
        Matter.World.clear(engineRef.current.world, false);
        Matter.Engine.clear(engineRef.current);
      }
      if (runnerRef.current) {
        Matter.Runner.stop(runnerRef.current);
      }
    };
  }, [dsl]);

  // 3. Dynamic Controls Handler
  const handleSliderChange = (paramId: string, bind: string, val: number) => {
    setParamValues(prev => ({ ...prev, [paramId]: val }));

    if (!engineRef.current) return;

    if (bind === 'environment.gravity.y') {
      engineRef.current.gravity.y = val;
    } else if (bind === 'environment.gravity.x') {
      engineRef.current.gravity.x = val;
    } else {
      let body: Matter.Body | undefined = undefined;
      const indexMatch = bind.match(/^objects\[(\d+)\]/);
      if (indexMatch) {
        const idx = parseInt(indexMatch[1]);
        body = bodyRefs.current[idx];
      } else {
        const idMatch = bind.match(/^objects\[['"]?([^'"]+)['"]?\]/);
        if (idMatch) {
          const id = idMatch[1];
          body = bodyMapRef.current[id];
        }
      }

      if (body) {
        if (bind.endsWith('.physics.mass')) {
          Matter.Body.setMass(body, val);
        } else if (bind.endsWith('.material.restitution')) {
          body.restitution = val;
        } else if (bind.endsWith('.material.friction')) {
          body.friction = val;
        } else if (bind.endsWith('.velocity.x')) {
          Matter.Body.setVelocity(body, { x: val * (scaleFactor.x / 10), y: body.velocity.y });
        } else if (bind.endsWith('.velocity.y')) {
          Matter.Body.setVelocity(body, { x: body.velocity.x, y: val * (scaleFactor.y / 10) });
        }
      }
    }
  };

  const handleToggleChange = (paramId: string, bind: string, active: boolean) => {
    setParamValues(prev => ({ ...prev, [paramId]: active ? 1 : 0 }));
    
    if (!engineRef.current) return;
    if (bind.includes('airResistance') || bind.includes('active')) {
      dsl.objects.forEach((obj) => {
        const body = bodyMapRef.current[obj.id];
        if (body && !body.isStatic) {
          body.frictionAir = active ? (dsl.environment.airResistance || 0.02) : 0.0;
        }
      });
    }
  };

  // Playback Action Helpers
  const handleStartPause = () => {
    if (!runnerRef.current || !engineRef.current) return;
    if (isPaused) {
      Matter.Runner.run(runnerRef.current, engineRef.current);
      setIsPaused(false);
    } else {
      Matter.Runner.stop(runnerRef.current);
      setIsPaused(true);
    }
  };

  const handleReset = () => {
    if (!engineRef.current) return;

    dsl.objects.forEach((obj) => {
      const body = bodyMapRef.current[obj.id];
      if (body) {
        const px = obj.position.x * scaleFactor.x;
        const py = obj.position.y * scaleFactor.y;
        
        Matter.Body.setPosition(body, { x: px, y: py });
        const vx = (obj.velocity?.x || 0) * (scaleFactor.x / 10);
        const vy = (obj.velocity?.y || 0) * (scaleFactor.y / 10);
        Matter.Body.setVelocity(body, { x: vx, y: vy });
        Matter.Body.setAngle(body, (obj as any).rotation || 0);
        Matter.Body.setAngularVelocity(body, 0);
      }
    });

    // Reset controls to defaults
    const initialParams: Record<string, number> = {};
    dsl.controls.parameters.forEach((param) => {
      if (param.type === 'slider') {
        let val = (param.min! + param.max!) / 2;
        if (param.bind === 'environment.gravity.y') {
          val = dsl.environment.gravity.y;
        } else if (param.bind === 'environment.gravity.x') {
          val = dsl.environment.gravity.x;
        } else {
          const match = param.bind.match(/^objects\[(\d+)\]\.physics\.mass$/);
          if (match) {
            const idx = parseInt(match[1]);
            val = dsl.objects[idx]?.physics.mass || 1.0;
          } else {
            const idMatch = param.bind.match(/^objects\[['"]?([^'"]+)['"]?\]\.physics\.mass$/);
            if (idMatch) {
              const id = idMatch[1];
              val = dsl.objects.find(o => o.id === id)?.physics.mass || 1.0;
            }
          }
        }
        initialParams[param.id] = val;
        handleSliderChange(param.id, param.bind, val);
      } else if (param.type === 'toggle') {
        initialParams[param.id] = 1;
        handleToggleChange(param.id, param.bind, true);
      }
    });
    setParamValues(initialParams);
  };

  // 4. Mathematical Equation & Telemetry Variable Resolver
  const resolveVariableValue = (path: string, binding?: FormulaBinding): number => {
    if (path.startsWith('environment.gravity.y')) {
      return engineRef.current?.gravity.y || 0;
    }
    if (path.startsWith('environment.gravity.x')) {
      return engineRef.current?.gravity.x || 0;
    }

    let body: Matter.Body | undefined = undefined;
    let subPath = '';
    
    const indexMatch = path.match(/^objects\[(\d+)\]\.(.+)$/);
    if (indexMatch) {
      const idx = parseInt(indexMatch[1]);
      body = bodyRefs.current[idx];
      subPath = indexMatch[2];
    } else {
      const idMatch = path.match(/^objects\[['"]?([^'"]+)['"]?\]\.(.+)$/);
      if (idMatch) {
        const id = idMatch[1];
        body = bodyMapRef.current[id];
        subPath = idMatch[2];
      }
    }

    if (body) {
      if (subPath === 'physics.mass') return body.mass;
      if (subPath === 'material.friction') return body.friction;
      if (subPath === 'position.y') {
        const heightVal = Math.max(0, (canvasHeight - body.position.y) / scaleFactor.y);
        return heightVal;
      }
      if (subPath === 'position.x') return body.position.x / scaleFactor.x;
      if (subPath === 'velocity.y') {
        return -body.velocity.y / (scaleFactor.y / 10);
      }
      if (subPath === 'velocity.x') {
        return body.velocity.x / (scaleFactor.x / 10);
      }
      if (subPath === 'velocity.magnitude') {
        const vel = Math.sqrt(body.velocity.x * body.velocity.x + body.velocity.y * body.velocity.y);
        return vel / (scaleFactor.x / 10);
      }
    }

    // Generic formula evaluation for dependent variables if a binding is passed!
    if (binding && path.startsWith('runtime.calculated')) {
      const formulaStr = binding.formula.toLowerCase();
      
      const resolvedVars: Record<string, number> = {};
      Object.entries(binding.variables).forEach(([symbol, info]) => {
        if (info.role === 'independent') {
          resolvedVars[symbol.toLowerCase()] = resolveVariableValue(info.path);
        }
      });

      const m = resolvedVars['m'] ?? (resolvedVars['mass'] ?? (bodyRefs.current[0]?.mass ?? 1.0));
      const g = resolvedVars['g'] ?? (engineRef.current?.gravity.y ?? 1.0);
      const h = resolvedVars['h'] ?? (bodyRefs.current[0] ? Math.max(0, (canvasHeight - bodyRefs.current[0].position.y) / scaleFactor.y) : 0);
      const v = resolvedVars['v'] ?? (bodyRefs.current[0] ? Math.sqrt(bodyRefs.current[0].velocity.x * bodyRefs.current[0].velocity.x + bodyRefs.current[0].velocity.y * bodyRefs.current[0].velocity.y) / 10 : 0);
      const a = resolvedVars['a'] ?? g;
      const L = resolvedVars['l'] ?? 5.0;

      if (formulaStr.includes('pe =') || formulaStr.includes('mgh')) {
        return m * g * h;
      }
      if (formulaStr.includes('ke =') || formulaStr.includes('1/2mv')) {
        return 0.5 * m * v * v;
      }
      if (formulaStr.includes('w =') || formulaStr.includes('mg')) {
        return m * g;
      }
      if (formulaStr.includes('f =') || formulaStr.includes('ma')) {
        return m * a;
      }
      if (formulaStr.includes('t =') || formulaStr.includes('l/g')) {
        return 2 * Math.PI * Math.sqrt(L / g);
      }
    }

    if (path.startsWith('runtime.calculated.potentialEnergy')) {
      const body = bodyRefs.current[0];
      const g = engineRef.current?.gravity.y || 0;
      if (body) {
        const h = Math.max(0, (canvasHeight - body.position.y) / scaleFactor.y);
        return body.mass * g * h;
      }
    }
    if (path.startsWith('runtime.calculated.kineticEnergy')) {
      const body = bodyRefs.current[0];
      if (body) {
        const v = Math.sqrt(body.velocity.x * body.velocity.x + body.velocity.y * body.velocity.y) / 10;
        return 0.5 * body.mass * v * v;
      }
    }
    if (path.startsWith('runtime.calculated.acceleration')) {
      const body = bodyRefs.current[0];
      if (body && !body.isStatic) {
        return engineRef.current?.gravity.y || 0;
      }
    }
    if (path.startsWith('runtime.calculated.period')) {
      const g = engineRef.current?.gravity.y || 1;
      return 2 * Math.PI * Math.sqrt(5 / g);
    }

    return 0;
  };


  // Render Visual Helpers based on custom vectors
  const renderObjectGraphics = (obj: SimulationObject) => {
    const x = obj.position.x * scaleFactor.x;
    const y = obj.position.y * scaleFactor.y;
    const color = obj.visual.color || '#3b82f6';
    
    // Detect custom object identities from labels or ids
    const typeLabel = (obj.visual.label || obj.id).toLowerCase();
    const isApple = typeLabel.includes('apple') || obj.visual.asset?.assetId === 'apple';
    const isEarth = typeLabel.includes('earth') || obj.visual.asset?.assetId === 'planet_earth';
    const isMoon = typeLabel.includes('moon') || obj.visual.asset?.assetId === 'moon';
    const isSun = typeLabel.includes('sun') || obj.visual.asset?.assetId === 'sun';
    const isCrate = typeLabel.includes('crate') || obj.visual.asset?.assetId === 'crate_wooden';

    if (obj.shape.type === 'circle') {
      const r = (obj.shape.radius || 1) * scaleFactor.x;

      if (isApple) {
        return (
          <g>
            {/* Apple body */}
            <path
              d={`M ${x} ${y - r*0.3} 
                  C ${x + r*0.8} ${y - r*0.4}, ${x + r*1.1} ${y + r*0.2}, ${x + r*0.9} ${y + r*0.7} 
                  C ${x + r*0.7} ${y + r*1.1}, ${x} ${y + r*1.2}, ${x} ${y + r*1.1} 
                  C ${x} ${y + r*1.2}, ${x - r*0.7} ${y + r*1.1}, ${x - r*0.9} ${y + r*0.7} 
                  C ${x - r*1.1} ${y + r*0.2}, ${x - r*0.8} ${y - r*0.4}, ${x} ${y - r*0.3} Z`}
              fill="url(#grad_apple)"
              filter="url(#fx_shadow)"
            />
            {/* Glossy highlight */}
            <path
              d={`M ${x - r*0.5} ${y - r*0.1} Q ${x - r*0.6} ${y + r*0.2}, ${x - r*0.3} ${y + r*0.5}`}
              fill="none"
              stroke="#ffffff"
              strokeWidth="2.5"
              strokeLinecap="round"
              opacity="0.5"
            />
            {/* Stem */}
            <path
              d={`M ${x} ${y - r*0.3} Q ${x + r*0.2} ${y - r*0.8}, ${x + r*0.5} ${y - r*0.9}`}
              fill="none"
              stroke="#7c2d12"
              strokeWidth="3.5"
              strokeLinecap="round"
            />
            {/* Leaf */}
            <path
              d={`M ${x + r*0.25} ${y - r*0.6} C ${x + r*0.6} ${y - r*0.8}, ${x + r*0.9} ${y - r*0.6}, ${x + r*0.6} ${y - r*0.45} Z`}
              fill="#22c55e"
              stroke="#15803d"
              strokeWidth="1"
            />
          </g>
        );
      }

      if (isEarth) {
        return (
          <g>
            <circle cx={x} cy={y} r={r} fill="#1d4ed8" filter="url(#fx_shadow)" />
            {/* Glowing Atmosphere */}
            <circle cx={x} cy={y} r={r} fill="none" stroke="#00eeff" strokeWidth="2.5" filter="url(#fx_glow_cyan)" opacity="0.6" />
            {/* Continents (dynamic vector path) */}
            <path
              d={`M ${x - r*0.6} ${y - r*0.2} Q ${x - r*0.3} ${y - r*0.6}, ${x} ${y - r*0.4} 
                  Q ${x + r*0.4} ${y - r*0.6}, ${x + r*0.6} ${y - r*0.1} 
                  T ${x - r*0.2} ${y + r*0.5} Z`}
              fill="#22c55e"
              opacity="0.85"
            />
            <path
              d={`M ${x - r*0.4} ${y + r*0.3} C ${x - r*0.2} ${y + r*0.6}, ${x + r*0.2} ${y + r*0.5}, ${x + r*0.3} ${y + r*0.2} Z`}
              fill="#22c55e"
              opacity="0.85"
            />
          </g>
        );
      }

      if (isMoon) {
        return (
          <g>
            <circle cx={x} cy={y} r={r} fill="url(#grad_moon)" filter="url(#fx_shadow)" />
            {/* Craters */}
            <circle cx={x - r*0.3} cy={y - r*0.2} r={r*0.22} fill="#64748b" opacity="0.4" />
            <circle cx={x + r*0.2} cy={y + r*0.3} r={r*0.15} fill="#64748b" opacity="0.4" />
            <circle cx={x + r*0.4} cy={y - r*0.3} r={r*0.12} fill="#64748b" opacity="0.3" />
          </g>
        );
      }

      if (isSun) {
        return (
          <g>
            <circle cx={x} cy={y} r={r} fill="url(#grad_sun)" filter="url(#fx_glow_yellow)" />
            <circle cx={x} cy={y} r={r * 0.9} fill="url(#grad_sun)" />
          </g>
        );
      }

      // Default glossy circle/ball
      return (
        <g>
          <circle cx={x} cy={y} r={r} fill="url(#grad_metal)" filter="url(#fx_shadow)" />
          <circle cx={x} cy={y} r={r} fill={color} opacity="0.3" />
          {/* Inner specular ring highlights */}
          <circle cx={x - r*0.3} cy={y - r*0.3} r={r * 0.25} fill="#ffffff" opacity="0.25" filter="url(#fx_glow_cyan)" />
        </g>
      );
    } else {
      // Rectangle shape
      const w = (obj.shape.width || 2) * scaleFactor.x;
      const h = (obj.shape.height || 2) * scaleFactor.y;

      if (isCrate) {
        return (
          <g>
            <rect x={x - w/2} y={y - h/2} width={w} height={h} rx="4" fill="#b45309" stroke="#78350f" strokeWidth="2.5" filter="url(#fx_shadow)" />
            {/* Diagonal planks */}
            <line x1={x - w/2 + 4} y1={y - h/2 + 4} x2={x + w/2 - 4} y2={y + h/2 - 4} stroke="#78350f" strokeWidth="2" />
            <line x1={x + w/2 - 4} y1={y - h/2 + 4} x2={x - w/2 + 4} y2={y + h/2 - 4} stroke="#78350f" strokeWidth="2" />
            {/* Bevel rim */}
            <rect x={x - w/2 + 3} y={y - h/2 + 3} width={w - 6} height={h - 6} fill="none" stroke="#d97706" strokeWidth="1.5" opacity="0.4" />
          </g>
        );
      }

      // Default mechanical platform/rectangle block
      return (
        <rect
          x={x - w/2}
          y={y - h/2}
          width={w}
          height={h}
          rx="4"
          fill="url(#grad_metal)"
          stroke={color}
          strokeWidth="2"
          filter="url(#fx_shadow)"
        />
      );
    }
  };

  return (
    <div className="flex-1 flex flex-col md:flex-row gap-4 h-full min-h-[500px]">
      
      {/* 1. Left Interactive Viewport Panel */}
      <div 
        ref={containerRef}
        className="flex-1 glass-panel rounded-xl overflow-hidden relative shadow-2xl engineering-grid min-h-[400px] border border-physics-border flex flex-col"
      >
        {/* Top Control Bar */}
        <div className="absolute top-0 left-0 right-0 h-12 bg-slate-950/80 border-b border-physics-border flex items-center justify-between px-5 z-20">
          <div className="flex items-center space-x-2">
            <Activity className="w-4 h-4 text-physics-neonCyan animate-pulse" />
            <span className="font-mono text-xs font-bold text-slate-300 tracking-wider uppercase" title={prompt}>
              {dsl.meta.title} — LIVE ENGINE
            </span>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={handleStartPause}
              className={`p-2 rounded bg-slate-900 border border-physics-border hover:border-physics-neonCyan transition-all flex items-center space-x-1.5 font-mono text-[10px] font-bold ${
                isPaused ? 'text-physics-neonGreen hover:text-physics-neonGreen' : 'text-physics-neonYellow hover:text-physics-neonYellow'
              } cursor-pointer`}
            >
              {isPaused ? <Play className="w-3.5 h-3.5" fill="currentColor" /> : <Pause className="w-3.5 h-3.5" fill="currentColor" />}
              <span>{isPaused ? 'RESUME' : 'PAUSE'}</span>
            </button>
            <button
              onClick={handleReset}
              className="p-2 rounded bg-slate-900 border border-physics-border hover:border-physics-neonCyan text-physics-neonCyan transition-all flex items-center space-x-1.5 font-mono text-[10px] font-bold cursor-pointer"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>RESET</span>
            </button>
          </div>
        </div>

        {/* Dynamic compiled SVG Canvas */}
        <svg
          ref={svgRef}
          className="flex-1 w-full h-full select-none cursor-grab active:cursor-grabbing mt-12 bg-slate-950/20"
          viewBox={`0 0 ${canvasWidth} ${canvasHeight}`}
          xmlns="http://www.w3.org/2000/svg"
        >
          <defs>
            {/* Gradients */}
            <radialGradient id="grad_apple" cx="35%" cy="30%" r="65%">
              <stop offset="0%" stopColor="#f87171" />
              <stop offset="50%" stopColor="#ef4444" />
              <stop offset="90%" stopColor="#991b1b" />
              <stop offset="100%" stopColor="#450a0a" />
            </radialGradient>
            
            <radialGradient id="grad_moon" cx="30%" cy="35%" r="70%">
              <stop offset="0%" stopColor="#f1f5f9" />
              <stop offset="60%" stopColor="#cbd5e1" />
              <stop offset="100%" stopColor="#475569" />
            </radialGradient>

            <radialGradient id="grad_sun" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#ffffff" />
              <stop offset="25%" stopColor="#fef08a" />
              <stop offset="55%" stopColor="#f97316" />
              <stop offset="100%" stopColor="#ef4444" stopOpacity="0" />
            </radialGradient>

            <linearGradient id="grad_metal" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#334155" />
              <stop offset="50%" stopColor="#1e293b" />
              <stop offset="100%" stopColor="#0f172a" />
            </linearGradient>

            <filter id="fx_shadow" x="-10%" y="-10%" width="120%" height="130%">
              <feDropShadow dx="0" dy="8" stdDeviation="6" floodColor="#000000" floodOpacity="0.6" />
            </filter>
            
            <filter id="fx_glow_cyan" x="-30%" y="-30%" width="160%" height="160%">
              <feGaussianBlur stdDeviation="8" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>

            <filter id="fx_glow_yellow" x="-30%" y="-30%" width="160%" height="160%">
              <feGaussianBlur stdDeviation="15" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {/* Grid Blueprint */}
          <g stroke="rgba(0, 238, 255, 0.03)" strokeWidth="1">
            {Array.from({ length: 20 }).map((_, i) => (
              <line key={`x-${i}`} x1={i * 50} y1={0} x2={i * 50} y2={canvasHeight} />
            ))}
            {Array.from({ length: 12 }).map((_, i) => (
              <line key={`y-${i}`} x1={0} y1={i * 50} x2={canvasWidth} y2={i * 50} />
            ))}
          </g>

          {/* Render Boundaries */}
          {(dsl.environment as any).boundaries?.enabled !== false && (
            <rect
              x="0"
              y={canvasHeight - 30}
              width={canvasWidth}
              height="30"
              fill="url(#grad_metal)"
              stroke="#1e293b"
              strokeWidth="2"
            />
          )}

          {/* Render Constraints dynamically */}
          {activeConstraints.map((c) => {
            let x1 = 0;
            let y1 = 0;
            
            if (c.constraint.bodyA) {
              const localOffset = c.constraint.pointA || { x: 0, y: 0 };
              x1 = c.constraint.bodyA.position.x + localOffset.x;
              y1 = c.constraint.bodyA.position.y + localOffset.y;
            } else if (c.constraint.pointA) {
              x1 = c.constraint.pointA.x;
              y1 = c.constraint.pointA.y;
            }
            
            const localOffsetB = c.constraint.pointB || { x: 0, y: 0 };
            const bodyB = c.constraint.bodyB!;
            const x2 = bodyB.position.x + localOffsetB.x;
            const y2 = bodyB.position.y + localOffsetB.y;
            
            return (
              <line
                key={c.id}
                x1={x1}
                y1={y1}
                x2={x2}
                y2={y2}
                stroke={c.color}
                strokeWidth={c.lineWidth}
                strokeDasharray={c.color === '#00eeff' ? '4 2' : undefined}
                filter={c.color === '#00eeff' ? 'url(#fx_glow_cyan)' : undefined}
              />
            );
          })}

          {/* Main Visual Objects Group */}
          <g id="simulation_entities">
            {dsl.objects.map((obj) => (
              <g key={obj.id} id={`phys_${obj.id}`}>
                {renderObjectGraphics(obj)}
                
                {/* Visual labels */}
                {obj.visual.showLabel !== false && (
                  <text
                    x={obj.position.x * scaleFactor.x}
                    y={obj.position.y * scaleFactor.y - ((obj.shape.radius || 1) * scaleFactor.x + 10)}
                    fill="#e2e8f0"
                    fontFamily="monospace"
                    fontSize="10"
                    fontWeight="bold"
                    textAnchor="middle"
                    className="select-none pointer-events-none drop-shadow"
                  >
                    {obj.visual.label || obj.id.toUpperCase()}
                  </text>
                )}
              </g>
            ))}
          </g>
        </svg>

        {/* Blueprint coordinate indicators overlay */}
        <div className="absolute bottom-3 left-4 font-mono text-[9px] text-slate-500 flex space-x-4 z-20 pointer-events-none">
          <span>WORLD SCALING: {scaleFactor.x}px/unit</span>
          <span>INTERACTION: MATTER-JS DRAG ON</span>
        </div>
      </div>

      {/* 2. Right Telemetry, controls & formulas panel */}
      <div className="w-full md:w-[360px] flex flex-col gap-4 shrink-0 overflow-y-auto max-h-[600px] pr-1">
        
        {/* A. Formula & Equation Solver Panel */}
        {dsl.formulaBindings.length > 0 && (
          <div className="glass-panel rounded-xl p-5 relative overflow-hidden shadow-2xl border border-physics-border">
            <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-physics-neonCyan to-physics-neonMagenta" />
            <div className="flex items-center space-x-2 mb-4">
              <Cpu className="w-5 h-5 text-physics-neonCyan" />
              <h2 className="font-mono text-sm font-bold text-slate-200 tracking-wider">FORMULA TELEMETRY SOLVER</h2>
            </div>

            <div className="space-y-4">
              {dsl.formulaBindings.map((bind) => (
                <div key={bind.id} className="glass-card p-3 rounded-lg border border-physics-border/60">
                  <div className="text-[10px] font-mono text-physics-neonCyan font-bold mb-1 tracking-widest uppercase">
                    {bind.id.replace(/_/g, ' ')}
                  </div>
                  
                  {/* Styled Formula math expression */}
                  <div className="font-mono text-base text-slate-100 bg-slate-950/60 p-2 rounded text-center font-bold mb-2.5 border border-physics-border/40 shadow-inner">
                    {bind.formula}
                  </div>

                  {/* Variables listing with dynamic real-time computed solvers */}
                  <div className="space-y-1.5 font-mono text-[11px]">
                    {Object.entries(bind.variables).map(([varSymbol, varMeta]) => {
                      const val = resolveVariableValue(varMeta.path, bind);
                      
                      return (
                        <div key={varSymbol} className="flex justify-between items-center text-slate-400 py-0.5 border-b border-physics-border/20">
                          <div className="flex items-center space-x-1.5">
                            <span className="text-physics-neonYellow font-bold">{varSymbol}</span>
                            <span className="text-[9px] text-slate-600">({varMeta.role})</span>
                          </div>
                          <span className="text-slate-100 font-bold">
                            {val.toFixed(2)}
                            <span className="text-[9px] text-slate-500 ml-1">
                              {varSymbol === 'm' ? 'kg' : varSymbol === 'g' ? 'm/s²' : varSymbol === 'h' ? 'm' : varSymbol === 'PE' || varSymbol === 'KE' ? 'J' : varSymbol === 'v' ? 'm/s' : varSymbol === 'F' ? 'N' : ''}
                            </span>
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* B. Controls Panel */}
        {dsl.controls.parameters.length > 0 && (
          <div className="glass-panel rounded-xl p-5 relative overflow-hidden shadow-2xl border border-physics-border">
            <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-physics-neonMagenta to-physics-neonYellow" />
            <div className="flex items-center space-x-2 mb-4">
              <Sliders className="w-5 h-5 text-physics-neonMagenta" />
              <h2 className="font-mono text-sm font-bold text-slate-200 tracking-wider">PARAMETER CONTROLS</h2>
            </div>

            <div className="space-y-4">
              {dsl.controls.parameters.map((param) => (
                <div key={param.id} className="space-y-2">
                  <div className="flex justify-between items-center font-mono text-xs">
                    <span className="text-slate-300 font-bold uppercase tracking-wider">{param.label}</span>
                    <span className="text-physics-neonYellow font-bold">
                      {paramValues[param.id] !== undefined ? paramValues[param.id].toFixed(2) : ''}
                      <span className="text-[9px] text-slate-500 font-normal ml-0.5">{param.symbol || ''}</span>
                    </span>
                  </div>

                  {param.type === 'slider' ? (
                    <div className="space-y-2">
                      <input
                        type="range"
                        min={param.min}
                        max={param.max}
                        step={param.step || 0.1}
                        value={paramValues[param.id] || 0}
                        onChange={(e) => handleSliderChange(param.id, param.bind, parseFloat(e.target.value))}
                        className="w-full h-1 bg-slate-900 border border-physics-border rounded-lg appearance-none cursor-pointer accent-physics-neonCyan focus:outline-none"
                      />
                      
                      {/* Planetary Presets row for Gravity parameter */}
                      {param.bind === 'environment.gravity.y' && (
                        <div className="flex flex-wrap gap-1 mt-2 bg-slate-950/60 p-2 rounded border border-physics-border/40">
                          {[
                            { label: '🌌 Zero-G', val: 0.0, name: 'Space' },
                            { label: '🌙 Moon', val: 1.6, name: 'Moon' },
                            { label: '🔴 Mars', val: 3.7, name: 'Mars' },
                            { label: '🌍 Earth', val: 9.8, name: 'Earth' },
                            { label: '🪐 Jupiter', val: 24.0, name: 'Jupiter' }
                          ].map((planet) => (
                            <button
                              key={planet.name}
                              onClick={() => {
                                // Scale value relative to earth's original DSL value (if DSL earth gravity is 1.0, moon is 1.6/9.8 = 0.16)
                                const dslEarthGravity = dsl.environment.gravity.y || 1.0;
                                const normalizedVal = (planet.val / 9.8) * dslEarthGravity;
                                handleSliderChange(param.id, param.bind, normalizedVal);
                              }}
                              className={`text-[9px] font-mono px-2 py-1 rounded transition-all cursor-pointer border ${
                                Math.abs((paramValues[param.id] || 0) - (planet.val / 9.8) * (dsl.environment.gravity.y || 1.0)) < 0.15
                                  ? 'bg-physics-neonCyan border-physics-neonCyan text-slate-950 font-bold shadow-[0_0_8px_rgba(0,238,255,0.3)]'
                                  : 'bg-slate-900 border-physics-border text-slate-400 hover:text-slate-100 hover:border-physics-neonCyan'
                              }`}
                            >
                              {planet.label}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="flex items-center">
                      <button
                        onClick={() => handleToggleChange(param.id, param.bind, !paramValues[param.id])}
                        className={`w-10 h-5 rounded-full p-0.5 transition-all flex items-center ${
                          paramValues[param.id] === 1 ? 'bg-physics-neonGreen justify-end' : 'bg-slate-900 border border-physics-border justify-start'
                        }`}
                      >
                        <motion.div layout className="w-4 h-4 rounded-full bg-slate-100 shadow" />
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* C. Real-Time Observables & Telemetry Dashboard */}
        {dsl.observables.length > 0 && (
          <div className="glass-panel rounded-xl p-5 relative overflow-hidden shadow-2xl border border-physics-border">
            <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-physics-neonYellow to-physics-neonGreen" />
            <div className="flex items-center space-x-2 mb-4">
              <Activity className="w-5 h-5 text-physics-neonGreen" />
              <h2 className="font-mono text-sm font-bold text-slate-200 tracking-wider">LIVE TELEMETRY GAUGE</h2>
            </div>

            <div className="grid grid-cols-2 gap-3">
              {dsl.observables.map((obs) => {
                const val = resolveVariableValue(obs.source);
                return (
                  <div key={obs.id} className="glass-card p-3 rounded-lg border border-physics-border/60 flex flex-col justify-center">
                    <span className="font-mono text-[9px] text-slate-500 uppercase tracking-widest leading-none mb-1">
                      {obs.label}
                    </span>
                    <span className="font-mono text-base font-bold text-slate-100">
                      {val.toFixed(obs.precision)}
                      <span className="text-[10px] text-physics-neonCyan font-normal ml-0.5">{obs.unit || ''}</span>
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

      </div>
    </div>
  );
};

export default InteractiveSimulation;
