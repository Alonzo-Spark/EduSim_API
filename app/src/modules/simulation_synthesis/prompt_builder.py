import json
from datetime import datetime, timezone

# Example for the new Architecture - Optimized for Matter.js
EXAMPLE_RESPONSE = json.loads("""{
  "dsl": {
    "meta": {
      "id": "simulation_id",
      "title": "Simulation Title",
      "topic": "Physics Topic",
      "simulationType": "Mechanics",
      "difficulty": "Grade 6-10",
      "version": "3.0"
    },
    "environment": {
      "gravity": {
        "x": 0,
        "y": 1.0
      },
      "airResistance": 0.01,
      "background": {
        "color": "#0f172a"
      },
      "world": {
        "width": 20,
        "height": 12,
        "unitSystem": "normalized"
      },
      "camera": {
        "mode": "auto-fit",
        "padding": 0.15,
        "allowZoom": true,
        "allowPan": true
      },
      "boundaries": {
        "enabled": true,
        "type": "solid"
      }
    },
    "objects": [
      {
        "id": "object_1",
        "category": "physics-object",
        "bodyType": "dynamic",
        "shape": {
          "type": "circle",
          "radius": 1
        },
        "position": {
          "x": 5,
          "y": 5
        },
        "rotation": 0,
        "velocity": {
          "x": 0,
          "y": 0
        },
        "physics": {
          "mass": 5,
          "density": 1,
          "affectedByGravity": true,
          "fixedRotation": false,
          "isSensor": false
        },
        "material": {
          "friction": 0.2,
          "restitution": 0.5
        },
        "collision": {
          "enabled": true,
          "group": "default"
        },
        "visual": {
          "color": "#3b82f6",
          "label": "Object",
          "showLabel": true,
          "showVelocityVector": true,
          "showForceVector": false,
          "showTrail": false,
          "asset": {
                      "enabled": true,
                      "assetId": "ball_basket1",
                      "scale": 1,
                      "rotationSync": true,
                      "anchor": {
                        "x": 0.5,
                        "y": 0.5
                      }
                  }
        }
      },
      {
        "id": "ground",
        "category": "environment",
        "bodyType": "static",
        "shape": {
          "type": "rectangle",
          "width": 20,
          "height": 1
        },
        "position": {
          "x": 10,
          "y": 11.5
        },
        "physics": {
          "mass": 0,
          "affectedByGravity": false
        },
        "material": {
          "friction": 0.8,
          "restitution": 0
        },
        "visual": {
          "color": "#475569"
        }
      }
    ],
    "forces": [
      {
        "id": "force_1",
        "type": "constantForce",
        "target": "object_1",
        "vector": {
          "x": 5,
          "y": 0
        },
        "active": true
      }
    ],
    "constraints": [
      {
        "id": "constraint_1",
        "type": "rope",
        "bodyA": null,
        "bodyB": "object_1",
        "anchorA": {
          "x": 10,
          "y": 2
        },
        "anchorB": null,
        "length": 5,
        "stiffness": 0.9,
        "damping": 0.01,
        "breakable": false,
        "maxForce": null,
        "visual": {
          "visible": true,
          "color": "#ffffff",
          "lineWidth": 2
        }
      }
    ],
    "behaviors": [
      {
        "id": "air_drag",
        "type": "airDrag",
        "targets": ["object_1"],
        "coefficient": 0.01,
        "active": true
      }
    ],
    "interactions": [
      {
        "id": "drag_interaction",
        "type": "drag",
        "targets": ["object_1"]
      },
      {
        "id": "reset_interaction",
        "type": "reset",
        "targets": ["object_1"]
      }
    ],
    "formulaBindings": [
      {
        "id": "newtons_second_law",
        "formula": "F = ma",
        "variables": {
          "F": {
            "path": "forces[0].vector.x",
            "role": "independent"
          },
          "m": {
            "path": "objects[0].physics.mass",
            "role": "independent"
          },
          "a": {
            "path": "runtime.calculated.acceleration",
            "role": "dependent"
          }
        }
      },
      {
        "id": "kinetic_energy",
        "formula": "KE = 1/2mv^2",
        "variables": {
          "m": {
            "path": "objects[0].physics.mass",
            "role": "independent"
          },
          "v": {
            "path": "objects[0].velocity.magnitude",
            "role": "dependent"
          },
          "KE": {
            "path": "runtime.calculated.kineticEnergy",
            "role": "dependent"
          }
        }
      },
      {
        "id": "potential_energy",
        "formula": "PE = mgh",
        "variables": {
          "m": {
            "path": "objects[0].physics.mass",
            "role": "independent"
          },
          "g": {
            "path": "environment.gravity.y",
            "role": "independent"
          },
          "h": {
            "path": "objects[0].position.y",
            "role": "dependent"
          },
          "PE": {
            "path": "runtime.calculated.potentialEnergy",
            "role": "dependent"
          }
        }
      },
      {
        "id": "pendulum_period",
        "formula": "T = 2π√(L/g)",
        "variables": {
          "L": {
            "path": "constraints[0].length",
            "role": "independent"
          },
          "g": {
            "path": "environment.gravity.y",
            "role": "independent"
          },
          "T": {
            "path": "runtime.calculated.period",
            "role": "dependent"
          }
        }
      }
    ],
    "controls": {
      "parameters": [
        {
          "id": "gravity_slider",
          "type": "slider",
          "label": "Gravity",
          "symbol": "g",
          "bind": "environment.gravity.y",
          "min": 0,
          "max": 3,
          "step": 0.1
        },
        {
          "id": "mass_slider",
          "type": "slider",
          "label": "Mass",
          "symbol": "m",
          "bind": "objects[0].physics.mass",
          "min": 1,
          "max": 20,
          "step": 1
        },
        {
          "id": "force_slider",
          "type": "slider",
          "label": "Force",
          "symbol": "F",
          "bind": "forces[0].vector.x",
          "min": -20,
          "max": 20,
          "step": 1
        },
        {
          "id": "friction_slider",
          "type": "slider",
          "label": "Friction",
          "symbol": "μ",
          "bind": "objects[0].material.friction",
          "min": 0,
          "max": 1,
          "step": 0.01
        },
        {
          "id": "length_slider",
          "type": "slider",
          "label": "Constraint Length",
          "symbol": "L",
          "bind": "constraints[0].length",
          "min": 1,
          "max": 10,
          "step": 0.5
        },
        {
          "id": "air_drag_toggle",
          "type": "toggle",
          "label": "Air Resistance",
          "bind": "behaviors[0].active"
        }
      ],
      "actions": [
        {
          "id": "start_button",
          "type": "button",
          "label": "Start",
          "action": "startSimulation"
        },
        {
          "id": "pause_button",
          "type": "button",
          "label": "Pause",
          "action": "togglePause"
        },
        {
          "id": "reset_button",
          "type": "button",
          "label": "Reset",
          "action": "resetSimulation"
        }
      ]
    },
    "observables": [
      {
        "id": "velocity",
        "label": "Velocity",
        "source": "objects[0].velocity.magnitude",
        "precision": 2
      },
      {
        "id": "acceleration",
        "label": "Acceleration",
        "source": "runtime.calculated.acceleration",
        "precision": 2
      },
      {
        "id": "net_force",
        "label": "Net Force",
        "source": "runtime.calculated.netForce",
        "precision": 2
      },
      {
        "id": "kinetic_energy",
        "label": "Kinetic Energy",
        "source": "runtime.calculated.kineticEnergy",
        "precision": 2
      },
      {
        "id": "potential_energy",
        "label": "Potential Energy",
        "source": "runtime.calculated.potentialEnergy",
        "precision": 2
      },
      {
        "id": "period",
        "label": "Time Period",
        "source": "runtime.calculated.period",
        "precision": 2
      }
    ],
    "events": [
      {
        "id": "collision_event",
        "type": "collision",
        "targets": ["object_1", "ground"],
        "response": {
          "playSound": false,
          "showEffect": false
        }
      }
    ],
    "runtime": {
      "engine": "matter-js",
      "renderer": "pixi-js",
      "fps": 60,
      "scaling": {
        "mode": "dynamic-auto-fit",
        "baseUnit": 50,
        "allowResponsiveResize": true
      },
      "interaction": {
        "allowDragging": true,
        "allowZoom": true,
        "allowPan": true
      },
      "debug": false,
      "calculated": {
        "acceleration": 0,
        "netForce": 0,
        "kineticEnergy": 0,
        "potentialEnergy": 0,
        "momentum": 0,
        "period": 0
      }
    }
  },
  "knowledge": {
    "relevant_formulas": [
      "F = ma",
      "KE = 1/2mv^2",
      "PE = mgh",
      "T = 2π√(L/g)"
    ],
    "related_concepts": [
      "Force",
      "Motion",
      "Acceleration",
      "Energy",
      "Gravity",
      "Oscillation",
      "Constraints"
    ],
    "learningObjectives": [
      "Understand force and acceleration relationships",
      "Observe the effect of gravity and friction",
      "Explore energy transformations",
      "Understand oscillatory motion"
    ]
  },
  "metadata": {
    "subject": "Physics",
    "chapter": "Mechanics",
    "difficulty": "Intermediate",
    "curriculum": "SCERT Telangana",
    "simulationCategory": "Interactive Physics",
    "renderer": "Matter.js + PixiJS",
    "unitSystem": "normalized-educational-units",
    "tags": [
      "Physics",
      "Simulation",
      "Mechanics",
      "Force",
      "Motion",
      "Pendulum",
      "STEM"
    ]
  }
}""")

def build_dsl_prompt(user_prompt: str, context: str) -> str:
    now = datetime.now(timezone.utc).isoformat()

    return f"""
You are an AI Physics Simulation Architect for EduSim.

Generate a runtime-ready, educational, simulation-agnostic physics DSL compatible with:
- Matter.js physics runtime
- PixiJS renderer
- Dynamic runtime scaling
- Auto-fit camera systems

━━━━━━━━━━━━━━━
CORE ARCHITECTURE RULES
━━━━━━━━━━━━━━━

1. Use NORMALIZED EDUCATIONAL UNITS.
   - DO NOT use pixels.
   - DO NOT use strict SI realism.
   - Values should remain small, stable, and educational.

2. Gravity should generally remain in safe normalized ranges:
   Example:
   "gravity": {{"x": 0, "y": 1.0}}

3. The frontend runtime handles:
   - scaling
   - rendering
   - responsiveness
   - auto-fit camera
   - coordinate transforms

4. Generate ONLY simulation contracts (DSL).
   NEVER generate:
   - Matter.js code
   - PixiJS code
   - rendering logic
   - JavaScript functions

5. Positive X → right
6. Positive Y → down

7. Prevent overlapping objects unless intentionally required.

8. NEVER generate deprecated fields:
   - movable
   - groundFriction

9. Return ONLY valid JSON.

━━━━━━━━━━━━━━━
SIMULATION GENERATION RULES
━━━━━━━━━━━━━━━

1. The DSL must remain simulation-agnostic.

2. Generate ONLY the components required for the requested simulation.

3. Do NOT force:
   - ground objects
   - gravity
   - pendulums
   - collisions
   - sliders
   - formulas
   unless relevant to the prompt.

4. Constraints, forces, behaviors, controls, observables, and formulas should be dynamically generated based on the scenario.

5. Keep all systems generic and reusable.

━━━━━━━━━━━━━━━
REQUIRED ROOT SECTIONS
━━━━━━━━━━━━━━━

Always include:
- meta
- environment
- objects
- forces
- constraints
- behaviors
- interactions
- formulaBindings
- controls
- observables
- events
- runtime

Even if empty, return:
[]

━━━━━━━━━━━━━━━
OBJECT RULES
━━━━━━━━━━━━━━━

Every object MUST contain:
- id
- category
- bodyType
- shape
- position
- rotation
- velocity
- physics
- material
- visual

Allowed bodyType values:
- dynamic
- static
- kinematic

shape.type can include:
- circle
- rectangle
- polygon
- line

visual MUST contain:
- color

Optional visual fields:
- label
- showLabel
- showVelocityVector
- showForceVector
- showTrail

Optional visual.asset fields:
- enabled
- assetId
- scale
- rotationSync
- anchor

Example:
"asset": {{
  "enabled": false,
  "assetId": "planet_earth",
  "scale": 1,
  "rotationSync": true,
  "anchor": {{
    "x": 0.5,
    "y": 0.5
  }}
}}


━━━━━━━━━━━━━━━
ASSET RULES
━━━━━━━━━━━━━━━

1. Assets are OPTIONAL visual enhancements.

2. Primitive rendering should remain the default fallback.

3. Assets must NEVER affect physics calculations.

4. Physics bodies must remain simple geometric shapes.

5. Use assetId instead of external image URLs.

6. Do NOT generate remote asset URLs.

7. Assets should only be generated when visually meaningful for the simulation.

━━━━━━━━━━━━━━━
AVAILABLE ASSET LIBRARY
━━━━━━━━━━━━━━━

The following assets are pre-installed. Use the 'id' as the 'assetId' in the DSL:

1. Physics (ids): ball_blue, ball_red, ball_basket, weight_heavy, weight_light, spring_relaxed, spring_stretched, chain_link.
2. Vehicles (ids): car_blue_1, car_red_1, car_black_1, truck_delivery, ambulance, bus_school, motorcycle_blue, suv_military.
3. Space (ids): planet_earth, planet_mars, moon, sun, asteroid_large, spacecraft_apollo, satellite_dish.
4. Nature (ids): tree_oak, tree_pine, bush1, mushroom_red, cactus, wood_plank.
5. Misc (ids): crate_wooden, barrel_metal, target_red, flag_checkered, arrow_direction.

*Note: Always prefer these IDs over generic names to ensure images load correctly.*

━━━━━━━━━━━━━━━
FORCE RULES
━━━━━━━━━━━━━━━

Force types may include:
- constantForce
- impulse
- directionalForce
- gravitationalAttraction
- magneticForce

Every force should contain:
- id
- type
- target
- active

━━━━━━━━━━━━━━━
CONSTRAINT RULES
━━━━━━━━━━━━━━━

Constraints should remain generic and reusable.

Allowed constraint types may include:
- rope
- spring
- link
- distance
- joint

Generate constraints ONLY when required.

Constraint fields may include:
- bodyA
- bodyB
- anchorA
- anchorB
- length
- stiffness
- damping
- breakable
- maxForce
- visual

Constraint visual fields may include:
- visible
- color
- lineWidth

━━━━━━━━━━━━━━━
VISUAL RULES
━━━━━━━━━━━━━━━

1. Visual properties are rendering-only metadata.

2. Visual properties must NEVER affect physics behavior.

3. Renderable entities may contain:
- color
- label
- vectors
- trails
- assets

4. Primitive rendering should always work even if assets are missing.

5. Objects, constraints, and boundaries may contain visual configuration.

━━━━━━━━━━━━━━━
BEHAVIOR RULES
━━━━━━━━━━━━━━━

Behavior types may include:
- airDrag
- oscillation
- buoyancy
- attraction
- wavePropagation
- orbitMotion

Behaviors should remain reusable and simulation-agnostic.

━━━━━━━━━━━━━━━
INTERACTION RULES
━━━━━━━━━━━━━━━

Interactions represent user interactions.

Examples:
- drag
- reset
- spawn
- launch
- connect
- cut

━━━━━━━━━━━━━━━
FORMULA RULES
━━━━━━━━━━━━━━━

1. Include formulaBindings ONLY when educationally relevant.

2. Every formulaBinding MUST contain:
- id
- formula
- variables

3. Variables MUST contain:
- path
- role

Allowed roles:
- independent
- dependent

4. Dependent calculated values MUST use:
"runtime.calculated"

Example:
"runtime": {{
  "calculated": {{
    "kineticEnergy": 0
  }}
}}

5. Every important independent variable MAY generate:
- sliders
- toggles
- inputs

ONLY if interactive controls make sense.

6. Every important dependent variable should appear in observables.

━━━━━━━━━━━━━━━
CONTROL RULES
━━━━━━━━━━━━━━━

Controls are OPTIONAL.

Generate controls ONLY when useful for interaction.

Slider controls MUST contain:
- min
- max
- step
- bind

Buttons MUST contain:
- id
- type
- label
- action

Buttons MUST NOT contain:
- bind
- min
- max
- step

Allowed actions:
- startSimulation
- togglePause
- resetSimulation

━━━━━━━━━━━━━━━
OBSERVABLE RULES
━━━━━━━━━━━━━━━

Observables should expose important runtime values.

Examples:
- velocity
- acceleration
- force
- momentum
- kinetic energy
- potential energy
- displacement
- angular velocity
- voltage
- current
- frequency
- amplitude
- wavelength
- time period

Observables MUST contain:
- id
- label
- source

━━━━━━━━━━━━━━━
EVENT RULES
━━━━━━━━━━━━━━━

Events are OPTIONAL.

Examples:
- collision
- thresholdReached
- objectDestroyed
- constraintBroken
- goalReached

━━━━━━━━━━━━━━━
RUNTIME RULES
━━━━━━━━━━━━━━━

Always include runtime configuration.

The runtime section MUST contain:
- engine
- renderer
- fps
- scaling
- interaction
- calculated

Use:
"engine": "matter-js"
"renderer": "pixi-js"

Scaling MUST use:
"mode": "dynamic-auto-fit"

━━━━━━━━━━━━━━━
KNOWLEDGE RULES
━━━━━━━━━━━━━━━

Include ONLY:
- relevant_formulas
- related_concepts
- learningObjectives

━━━━━━━━━━━━━━━
METADATA RULES
━━━━━━━━━━━━━━━

Include:
- subject
- chapter
- difficulty
- curriculum
- simulationCategory
- renderer
- unitSystem
- tags

Use:
"unitSystem": "normalized-educational-units"

━━━━━━━━━━━━━━━
RESPONSE FORMAT
━━━━━━━━━━━━━━━

{{
  "dsl": {{}},
  "knowledge": {{}},
  "metadata": {{}}
}}

━━━━━━━━━━━━━━━
IMPORTANT GENERATION RULES
━━━━━━━━━━━━━━━

1. Generate ONLY components required for the simulation.
2. Avoid unnecessary controls or formulas.
3. Avoid mechanics-specific assumptions unless requested.
4. Keep structures reusable across all physics domains.
5. Maintain runtime-safe normalized values.
6. Ensure the simulation can scale dynamically.
7. Keep physics and rendering concerns separated.
8. Physics simulation must remain functional without assets.

━━━━━━━━━━━━━━━
DSL REFERENCE
━━━━━━━━━━━━━━━

{json.dumps(EXAMPLE_RESPONSE, indent=2)}

━━━━━━━━━━━━━━━
REFERENCE CONTEXT
━━━━━━━━━━━━━━━

{context}

━━━━━━━━━━━━━━━
TIMESTAMP
━━━━━━━━━━━━━━━

{now}

━━━━━━━━━━━━━━━
USER REQUEST
━━━━━━━━━━━━━━━

{user_prompt}

Return ONLY the valid JSON object.
"""
