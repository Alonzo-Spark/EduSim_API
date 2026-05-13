import json
from datetime import datetime, timezone

# Example for the new Architecture - Optimized for Matter.js
EXAMPLE_RESPONSE = {
  "dsl": {
    "meta": {
      "id": "simulation_id",
      "title": "Simulation Title",
      "topic": "Physics Topic",
      "simulationType": "Mechanics",
      "difficulty": "Grade 6-10",
      "version": "2.0"
    },

    "environment": {
      "gravity": {"x": 0.0, "y": 1.0},
      "airResistance": 0.005,
      "background": {"color": "#0f172a"},
      "world": {"width": 800, "height": 600},

      "units": {
        "length": "m",
        "mass": "kg",
        "time": "s",
        "force": "N",
        "energy": "J"
      },

      "boundaries": {
        "enabled": True
      }
    },

    "objects": [
      {
        "id": "object_1",
        "category": "physics-object",
        "type": "dynamicBody",

        "shape": {
          "type": "circle",
          "radius": 1.0
        },

        "position": {
          "x": 10.0,
          "y": 5.0
        },

        "velocity": {
          "x": 0.0,
          "y": 0.0
        },

        "initialState": {
          "angle": 45
        },

        "rotation": 0.0,

        "physics": {
          "mass": 5.0,
          "density": 1.0,
          "fixedRotation": False,
          "affectedByGravity": True,
          "isSensor": False
        },

        "material": {
          "friction": 0.05,
          "restitution": 0.3
        },

        "collision": {
          "enabled": True,
          "group": "default"
        },

        "visual": {
          "color": "#3b82f6",
          "label": "Physics Object",
          "showLabel": True,
          "showVelocityVector": True,
          "showTrail": False
        }
      }
    ],

    "forces": [
      {
        "id": "force_1",
        "type": "constantForce",
        "target": "object_1",

        "vector": {
          "x": 10.0,
          "y": 0.0
        },

        "active": False
      }
    ],

    "constraints": [
      {
        "id": "constraint_1",
        "type": "rope",

        "anchor": {
          "x": 5.0,
          "y": 2.0
        },

        "bodyB": "object_1",

        "length": 6.0,
        "stiffness": 0.9,

        "visual": {
          "color": "#ffffff",
          "lineWidth": 2
        }
      }
    ],

    "behaviors": [
      {
        "id": "drag_behavior",
        "type": "drag",
        "targets": ["object_1"],
        "coefficient": 0.01,
        "active": True
      }
    ],

    "formulaBindings": [
      {
        "formula": "F = ma",

        "variables": {
          "F": {
            "path": "forces[0].vector.x",
            "type": "independent"
          },

          "m": {
            "path": "objects[0].physics.mass",
            "type": "independent"
          },

          "a": {
            "path": "objects[0].acceleration.x",
            "type": "dependent"
          }
        }
      },

      {
        "formula": "KE = 1/2mv²",

        "variables": {
          "m": {
            "path": "objects[0].physics.mass",
            "type": "independent"
          },

          "v": {
            "path": "objects[0].velocity.magnitude",
            "type": "dependent"
          },

          "KE": {
            "path": "runtime.calculated.kineticEnergy",
            "type": "dependent"
          }
        }
      },

      {
        "formula": "PE = mgh",

        "variables": {
          "m": {
            "path": "objects[0].physics.mass",
            "type": "independent"
          },

          "g": {
            "path": "environment.gravity.y",
            "type": "independent"
          },

          "h": {
            "path": "objects[0].position.y",
            "type": "dependent"
          },

          "PE": {
            "path": "runtime.calculated.potentialEnergy",
            "type": "dependent"
          }
        }
      },

      {
        "formula": "f = μN",

        "variables": {
          "μ": {
            "path": "objects[0].material.friction",
            "type": "independent"
          },

          "N": {
            "path": "runtime.calculated.normalForce",
            "type": "dependent"
          },

          "f": {
            "path": "runtime.calculated.frictionForce",
            "type": "dependent"
          }
        }
      },

      {
        "formula": "T = 2π√(L/g)",

        "variables": {
          "L": {
            "path": "constraints[0].length",
            "type": "independent"
          },

          "g": {
            "path": "environment.gravity.y",
            "type": "independent"
          },

          "T": {
            "path": "runtime.calculated.period",
            "type": "dependent"
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

          "formulaReferences": [
            "F = ma",
            "PE = mgh",
            "T = 2π√(L/g)"
          ],

          "bind": "environment.gravity.y",

          "min": 0.0,
          "max": 20.0,
          "step": 0.1
        },

        {
          "id": "mass_slider",
          "type": "slider",
          "label": "Mass",
          "symbol": "m",

          "formulaReferences": [
            "F = ma",
            "KE = 1/2mv²",
            "PE = mgh"
          ],

          "bind": "objects[0].physics.mass",

          "min": 1.0,
          "max": 20.0,
          "step": 1.0
        },

        {
          "id": "force_slider",
          "type": "slider",
          "label": "Force",
          "symbol": "F",

          "formulaReferences": [
            "F = ma"
          ],

          "bind": "forces[0].vector.x",

          "min": 0.0,
          "max": 100.0,
          "step": 1.0
        },

        {
          "id": "friction_slider",
          "type": "slider",
          "label": "Friction",
          "symbol": "μ",

          "formulaReferences": [
            "f = μN"
          ],

          "bind": "objects[0].material.friction",

          "min": 0.0,
          "max": 1.0,
          "step": 0.01
        },

        {
          "id": "length_slider",
          "type": "slider",
          "label": "Length",
          "symbol": "L",

          "formulaReferences": [
            "T = 2π√(L/g)"
          ],

          "bind": "constraints[0].length",

          "min": 1.0,
          "max": 20.0,
          "step": 0.5
        },

        {
          "id": "drag_toggle",
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
        "unit": "m/s"
      },

      {
        "id": "acceleration",
        "label": "Acceleration",
        "source": "objects[0].acceleration.magnitude",
        "unit": "m/s²"
      },

      {
        "id": "force",
        "label": "Force",
        "source": "forces[0].vector.x",
        "unit": "N"
      },

      {
        "id": "kinetic_energy",
        "label": "Kinetic Energy",
        "source": "runtime.calculated.kineticEnergy",
        "unit": "J"
      },

      {
        "id": "potential_energy",
        "label": "Potential Energy",
        "source": "runtime.calculated.potentialEnergy",
        "unit": "J"
      },

      {
        "id": "friction_force",
        "label": "Friction Force",
        "source": "runtime.calculated.frictionForce",
        "unit": "N"
      },

      {
        "id": "normal_force",
        "label": "Normal Force",
        "source": "runtime.calculated.normalForce",
        "unit": "N"
      },

      {
        "id": "period",
        "label": "Time Period",
        "source": "runtime.calculated.period",
        "unit": "s"
      }
    ],

    "events": [],

    "runtime": {
      "engine": "matter-js",
      "renderer": "pixi-js",
      "fps": 60,
      "scale": 40,

      "paused": False,
      "allowDragging": True,
      "allowReset": True,
      "debug": False,

      "calculated": {
        "normalForce": 0,
        "frictionForce": 0,
        "netForce": 0,
        "kineticEnergy": 0,
        "potentialEnergy": 0,
        "period": 0
      }
    }
  },

  "knowledge": {
    "relevant_formulas": [
      "F = ma",
      "KE = 1/2mv²",
      "PE = mgh",
      "f = μN",
      "T = 2π√(L/g)"
    ],

    "related_concepts": [
      "Force",
      "Motion",
      "Acceleration",
      "Energy",
      "Gravity",
      "Friction",
      "Oscillation"
    ]
  },

  "metadata": {
    "subject": "Physics",
    "chapter": "Mechanics",
    "difficulty": "Intermediate",
    "curriculum": "SCERT Telangana",
    "simulationCategory": "Interactive Physics",
    "renderer": "Matter.js + PixiJS",

    "tags": [
      "Physics",
      "Simulation",
      "STEM",
      "Mechanics"
    ]
  }
}

def build_dsl_prompt(user_prompt: str, context: str) -> str:
    now = datetime.now(timezone.utc).isoformat()

    return f"""
You are an AI Physics Simulation Architect for EduSim.

Generate a runtime-ready, educational, Matter.js-compatible physics simulation DSL.

━━━━━━━━━━━━━━━
CORE RULES
━━━━━━━━━━━━━━━

1. Use SI units (meters), NOT pixels.
2. Use normalized gravity:
   "gravity": {{"x": 0.0, "y": 1.0}}
3. Allowed body types:
   - dynamicBody
   - staticBody
4. Static bodies MUST contain:
   "physics": {{"mass": 0.0, "isSensor": false}}
5. Positive X → right, Positive Y → down.
6. Prevent overlapping objects.
7. Never generate deprecated fields:
   - movable
   - groundFriction
8. Return ONLY valid JSON.

━━━━━━━━━━━━━━━
REQUIRED ROOT SECTIONS
━━━━━━━━━━━━━━━

Always include:
- objects
- forces
- constraints
- behaviors
- formulaBindings
- controls
- observables
- events

Even if empty, return [].

━━━━━━━━━━━━━━━
OBJECT RULES
━━━━━━━━━━━━━━━

Every object MUST contain:
- id
- category
- type
- shape
- position
- velocity
- rotation
- physics
- material
- visual

visual MUST contain:
- color
- label

━━━━━━━━━━━━━━━
FORMULA RULES
━━━━━━━━━━━━━━━

1. Every important independent formula variable should have:
   - slider
   - toggle
   - input control

2. Every dependent variable should appear in observables.

3. Every formulaBinding MUST contain:
- formula
- variables
- runtime paths
- variable type:
  - independent
  - dependent

4. Derived/calculated values MUST use:
"runtime.calculated"

Example:
"runtime": {{
  "calculated": {{
    "kineticEnergy": 0,
    "frictionForce": 0,
    "normalForce": 0
  }}
}}

━━━━━━━━━━━━━━━
CONTROL RULES
━━━━━━━━━━━━━━━

Sliders MUST contain:
- min
- max
- step

Buttons/toggles MUST NOT contain:
- min
- max
- step

Buttons MUST use actions:
- startSimulation
- togglePause
- resetSimulation

Never use bind for buttons.

━━━━━━━━━━━━━━━
OBSERVABLE RULES
━━━━━━━━━━━━━━━

Include when relevant:
- velocity
- acceleration
- force
- kinetic energy
- potential energy
- friction force
- normal force
- time period
- elapsed time

━━━━━━━━━━━━━━━
KNOWLEDGE RULES
━━━━━━━━━━━━━━━

Include ONLY:
- relevant_formulas
- related_concepts

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
- tags

━━━━━━━━━━━━━━━
RESPONSE FORMAT
━━━━━━━━━━━━━━━

{{
  "dsl": {{}},
  "knowledge": {{}},
  "metadata": {{}}
}}

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














