import json
import os

topics_data = {
    "gravity": {
        "concept": {
            "topic": "gravity",
            "concept_explanation": "Gravity is a fundamental force of nature that attracts objects toward each other. On Earth, it gives weight to physical objects and causes them to fall toward the ground with a constant acceleration.",
            "assets": ["ball", "box", "triangle"],
            "relationships": ["free_fall", "acceleration"],
            "difficulty": "beginner"
        },
        "formulas": [
            {
                "name": "Weight Formula",
                "latex": "F = mg",
                "explanation": "Weight equals mass multiplied by gravity ($g \\approx 9.81 m/s^2$)."
            }
        ],
        "hints": [
            {"text": "Observe how acceleration remains constant regardless of the object's mass."},
            {"text": "Compare the falling speed of light and heavy objects in the simulation."}
        ],
        "misconceptions": [
            "Heavier objects fall faster than lighter objects (ignoring air resistance).",
            "Gravity only exists on Earth."
        ],
        "experiments": [
            {"title": "Free Fall Observation", "description": "Drop two objects of different masses from the same height and watch them hit the ground simultaneously."}
        ]
    },
    "collisions": {
        "concept": {
            "topic": "collisions",
            "concept_explanation": "A collision occurs when two or more objects exert forces on each other over a relatively short time. The total momentum of an isolated system is always conserved before and after the impact.",
            "assets": ["ball", "box", "triangle"],
            "relationships": ["momentum", "impulse"],
            "difficulty": "intermediate"
        },
        "formulas": [
            {
                "name": "Momentum Formula",
                "latex": "p = mv",
                "explanation": "Momentum ($p$) is the product of an object's mass and its velocity."
            }
        ],
        "hints": [
            {"text": "Notice how kinetic energy changes during inelastic collisions."},
            {"text": "Observe that total momentum is always conserved upon impact."}
        ],
        "misconceptions": [
            "Kinetic energy is conserved in all collisions.",
            "Larger objects always transfer more force regardless of their speed."
        ],
        "experiments": [
            {"title": "Elastic vs Inelastic", "description": "Compare elastic vs inelastic impacts by crashing bouncy balls and heavy rigid boxes together."}
        ]
    },
    "projectile_motion": {
        "concept": {
            "topic": "projectile_motion",
            "concept_explanation": "Projectile motion is a form of motion experienced by an object or particle that is projected near the Earth's surface and moves along a curved path under the action of gravity only.",
            "assets": ["launcher_ball", "box"],
            "relationships": ["gravity", "kinematics"],
            "difficulty": "intermediate"
        },
        "formulas": [
            {
                "name": "Range Formula",
                "latex": "R = \\frac{v^2\\sin(2\\theta)}{g}",
                "explanation": "Calculates the maximum horizontal distance traveled by a projectile."
            }
        ],
        "hints": [
            {"text": "Notice the curved parabolic trajectory of the moving object."},
            {"text": "The launch angle directly affects the maximum range and height."}
        ],
        "misconceptions": [
            "The horizontal velocity of a projectile decreases over time (ignoring air resistance).",
            "A dropped ball will hit the ground before a horizontally fired ball."
        ],
        "experiments": [
            {"title": "Trajectory Arcs", "description": "Launch two balls at different angles (e.g. 30 and 60 degrees) and observe their landing spots."}
        ]
    },
    "hookes_law": {
        "concept": {
            "topic": "hookes_law",
            "concept_explanation": "Hooke's Law states that the force needed to extend or compress a spring by some distance is proportional to that distance. It demonstrates elastic restoring forces.",
            "assets": ["box", "ball"],
            "relationships": ["oscillation", "energy_conservation"],
            "difficulty": "intermediate"
        },
        "formulas": [
            {
                "name": "Hooke's Law",
                "latex": "F = -kx",
                "explanation": "The restoring force ($F$) is proportional to the displacement ($x$) by the spring constant ($k$)."
            }
        ],
        "hints": [
            {"text": "Greater extension creates a greater restoring force."},
            {"text": "Observe how springs oscillate around their equilibrium position."}
        ],
        "misconceptions": [
            "A spring can be stretched indefinitely without permanently deforming.",
            "The restoring force acts in the same direction as the displacement."
        ],
        "experiments": [
            {"title": "Oscillation Rates", "description": "Stretch springs with different masses attached to observe varying oscillation frequencies."}
        ]
    },
    "pendulum": {
        "concept": {
            "topic": "pendulum",
            "concept_explanation": "A simple pendulum consists of a mass attached to a string or rod. When displaced from its resting position, gravity acts as a restoring force, causing it to swing back and forth in an oscillatory motion.",
            "assets": ["ball", "box"],
            "relationships": ["gravity", "oscillation", "hookes_law"],
            "difficulty": "intermediate"
        },
        "formulas": [
            {
                "name": "Period of a Pendulum",
                "latex": "T = 2\\pi\\sqrt{\\frac{L}{g}}",
                "explanation": "The period ($T$) depends only on the length ($L$) and gravity ($g$), not the mass."
            }
        ],
        "hints": [
            {"text": "Notice that the time it takes to complete a swing does not depend on the mass."},
            {"text": "The pendulum swings highest at its initial release point."}
        ],
        "misconceptions": [
            "A heavier bob swings significantly faster than a lighter bob.",
            "The period of a pendulum depends on the angle of its swing (for large angles)."
        ],
        "experiments": [
            {"title": "Period Observation", "description": "Release a pendulum and watch how gravity perpetually drives its rotational swing."}
        ]
    },
    "friction": {
        "concept": {
            "topic": "friction",
            "concept_explanation": "Friction is the resistive force acting between two surfaces sliding or attempting to slide against each other. It opposes motion and converts kinetic energy into thermal energy.",
            "assets": ["box", "triangle"],
            "relationships": ["energy_conservation", "momentum"],
            "difficulty": "beginner"
        },
        "formulas": [
            {
                "name": "Frictional Force",
                "latex": "F_f = \\mu N",
                "explanation": "Friction equals the coefficient of friction ($\\mu$) times the normal force ($N$)."
            }
        ],
        "hints": [
            {"text": "Objects will eventually stop sliding on rough surfaces due to friction."},
            {"text": "Heavier objects generally experience stronger frictional forces."}
        ],
        "misconceptions": [
            "Friction only occurs between solid objects.",
            "Friction always hinders motion."
        ],
        "experiments": [
            {"title": "Sliding Blocks", "description": "Slide a box across the floor and observe how it gradually decelerates to a stop."}
        ]
    },
    "inclined_plane": {
        "concept": {
            "topic": "inclined_plane",
            "concept_explanation": "An inclined plane, also known as a ramp, is a flat supporting surface tilted at an angle. It allows objects to be raised with less force over a longer distance.",
            "assets": ["triangle", "box", "ball"],
            "relationships": ["gravity", "friction"],
            "difficulty": "beginner"
        },
        "formulas": [
            {
                "name": "Parallel Force Component",
                "latex": "F = mg\\sin(\\theta)",
                "explanation": "The component of gravity pulling the object down the incline."
            }
        ],
        "hints": [
            {"text": "A steeper incline causes a faster acceleration down the ramp."},
            {"text": "Balls will roll down inclines, whereas boxes will slide."}
        ],
        "misconceptions": [
            "The normal force on an incline is equal to the object's total weight.",
            "An object's mass affects its acceleration down a frictionless incline."
        ],
        "experiments": [
            {"title": "Ramp Slides", "description": "Drop a box onto a triangle wedge and observe the mechanics of sliding motion."}
        ]
    },
    "momentum": {
        "concept": {
            "topic": "momentum",
            "concept_explanation": "Momentum is a measurement of mass in motion. Any object that is moving has momentum, which is the product of its mass and its velocity.",
            "assets": ["ball", "box"],
            "relationships": ["collisions", "impulse"],
            "difficulty": "intermediate"
        },
        "formulas": [
            {
                "name": "Momentum",
                "latex": "p = mv",
                "explanation": "Momentum is conserved in isolated physical systems."
            }
        ],
        "hints": [
            {"text": "Heavy objects moving slowly can have the same momentum as light objects moving fast."},
            {"text": "Observe how momentum transfers when two objects collide."}
        ],
        "misconceptions": [
            "Motion always implies a continuous force is acting.",
            "Momentum and kinetic energy are the exact same thing."
        ],
        "experiments": [
            {"title": "Momentum Transfer", "description": "Crash a fast-moving small ball into a stationary heavy box to witness momentum transfer."}
        ]
    },
    "impulse": {
        "concept": {
            "topic": "impulse",
            "concept_explanation": "Impulse is the change in momentum of an object when a force is applied over a period of time. A large force over a short time yields the same impulse as a small force over a long time.",
            "assets": ["ball", "box"],
            "relationships": ["momentum", "collisions"],
            "difficulty": "intermediate"
        },
        "formulas": [
            {
                "name": "Impulse",
                "latex": "J = F\\Delta t",
                "explanation": "Impulse ($J$) equals the average force ($F$) multiplied by the time interval ($\\Delta t$)."
            }
        ],
        "hints": [
            {"text": "Bouncing collisions exert a greater impulse than sticking collisions."},
            {"text": "A softer landing increases collision time and decreases peak force."}
        ],
        "misconceptions": [
            "Impulse is only generated during extremely fast impacts.",
            "Impulse is a type of energy."
        ],
        "experiments": [
            {"title": "Bouncing Impacts", "description": "Drop a highly elastic ball onto the ground and analyze its forceful rebound."}
        ]
    },
    "energy_conservation": {
        "concept": {
            "topic": "energy_conservation",
            "concept_explanation": "The Law of Conservation of Energy states that the total energy of an isolated system remains constant; it is said to be conserved over time. Energy can neither be created nor destroyed.",
            "assets": ["ball", "box"],
            "relationships": ["gravity", "pendulum", "hookes_law"],
            "difficulty": "advanced"
        },
        "formulas": [
            {
                "name": "Conservation of Mechanical Energy",
                "latex": "KE + PE = \\text{constant}",
                "explanation": "The sum of kinetic and potential energy remains constant in a conservative field."
            }
        ],
        "hints": [
            {"text": "As an object falls, it trades potential energy for kinetic energy."},
            {"text": "In the real world, some kinetic energy is lost as heat due to friction."}
        ],
        "misconceptions": [
            "Energy can be permanently lost or used up in a closed system.",
            "Potential energy only depends on height."
        ],
        "experiments": [
            {"title": "Energy Trading", "description": "Watch a pendulum swap its height (potential energy) for speed (kinetic energy) at the bottom."}
        ]
    },
    "rotational_motion": {
        "concept": {
            "topic": "rotational_motion",
            "concept_explanation": "Rotational motion deals with the rotation of rigid bodies around an axis. It involves concepts like torque, angular velocity, and moment of inertia.",
            "assets": ["triangle", "box"],
            "relationships": ["circular_motion", "inclined_plane"],
            "difficulty": "advanced"
        },
        "formulas": [
            {
                "name": "Torque",
                "latex": "\\tau = rF\\sin(\\theta)",
                "explanation": "Torque ($\\tau$) is the rotational equivalent of linear force."
            }
        ],
        "hints": [
            {"text": "Force applied further from the axis of rotation produces more torque."},
            {"text": "Objects naturally resist changes to their rotational speed (moment of inertia)."}
        ],
        "misconceptions": [
            "All points on a rotating object move at the same linear speed.",
            "An object's mass is the only factor resisting its rotation."
        ],
        "experiments": [
            {"title": "Spinning Wedge", "description": "Drop a triangular wedge at an angle to observe complex rotational forces."}
        ]
    },
    "circular_motion": {
        "concept": {
            "topic": "circular_motion",
            "concept_explanation": "Circular motion is a movement of an object along the circumference of a circle or rotation along a circular path. Uniform circular motion has a constant angular rate of rotation and speed.",
            "assets": ["ball"],
            "relationships": ["rotational_motion", "gravity"],
            "difficulty": "advanced"
        },
        "formulas": [
            {
                "name": "Centripetal Force",
                "latex": "F_c = \\frac{mv^2}{r}",
                "explanation": "The inward force required to keep an object moving in a circle."
            }
        ],
        "hints": [
            {"text": "Without centripetal force, a spinning object will fly off in a straight line."},
            {"text": "Even at a constant speed, velocity changes constantly due to changing direction."}
        ],
        "misconceptions": [
            "Centrifugal force is a real outward force pushing objects away from the center.",
            "Objects in circular motion are not accelerating if their speed is constant."
        ],
        "experiments": [
            {"title": "Orbital Analogy", "description": "Visualize how tension in a string or gravitational pull acts as a centripetal anchor."}
        ]
    },
    "buoyancy": {
        "concept": {
            "topic": "buoyancy",
            "concept_explanation": "Buoyancy is an upward force exerted by a fluid that opposes the weight of an immersed object. Archimedes' principle states that the buoyant force equals the weight of the displaced fluid.",
            "assets": ["box", "ball"],
            "relationships": ["gravity"],
            "difficulty": "intermediate"
        },
        "formulas": [
            {
                "name": "Buoyant Force",
                "latex": "F_b = \\rho g V",
                "explanation": "Buoyant force equals fluid density ($\\rho$) $\\times$ gravity ($g$) $\\times$ displaced volume ($V$)."
            }
        ],
        "hints": [
            {"text": "Objects float if their density is less than the density of the fluid."},
            {"text": "The shape of an object can help it displace more water to increase buoyancy."}
        ],
        "misconceptions": [
            "Heavy objects always sink, regardless of their shape or volume.",
            "Buoyancy only applies to liquids, not gases."
        ],
        "experiments": [
            {"title": "Density Comparisons", "description": "Compare how light versus dense objects respond differently when immersed in fluids."}
        ]
    },
    "wave_motion": {
        "concept": {
            "topic": "wave_motion",
            "concept_explanation": "Wave motion is the transfer of energy and momentum from one point to another without the transport of matter. Examples include sound, light, and water ripples.",
            "assets": ["ball"],
            "relationships": ["oscillation", "hookes_law"],
            "difficulty": "advanced"
        },
        "formulas": [
            {
                "name": "Wave Speed",
                "latex": "v = f\\lambda",
                "explanation": "Wave velocity ($v$) equals frequency ($f$) multiplied by wavelength ($\\lambda$)."
            }
        ],
        "hints": [
            {"text": "Higher frequencies generally result in shorter wavelengths if speed is constant."},
            {"text": "Waves transfer energy, not physical material."}
        ],
        "misconceptions": [
            "Waves transport physical matter across distances.",
            "Loud sounds travel faster than soft sounds in the same medium."
        ],
        "experiments": [
            {"title": "Rhythmic Oscillations", "description": "Visualize how repeating oscillations mimic the propagation of physical waves."}
        ]
    },
    "electricity": {
        "concept": {
            "topic": "electricity",
            "concept_explanation": "Electricity is the set of physical phenomena associated with the presence and motion of matter that has a property of electric charge. It encompasses electrostatic fields and electrical currents.",
            "assets": ["ball"],
            "relationships": ["energy_conservation"],
            "difficulty": "advanced"
        },
        "formulas": [
            {
                "name": "Coulomb's Law",
                "latex": "F = k\\frac{q_1q_2}{r^2}",
                "explanation": "The electrostatic force between two point charges is inversely proportional to the square of their separation distance."
            }
        ],
        "hints": [
            {"text": "Like charges repel, while opposite charges attract."},
            {"text": "Electrical forces are significantly stronger than gravitational forces on small scales."}
        ],
        "misconceptions": [
            "Current gets 'used up' as it travels through a circuit.",
            "Batteries supply electrons to a circuit."
        ],
        "experiments": [
            {"title": "Charge Repulsion", "description": "Understand how identical charged particles exert powerful repelling forces on each other."}
        ]
    }
}

base_dir = "app/src/rag/curriculum"

dirs = ["concepts", "formulas", "hints", "misconceptions", "experiments"]
for d in dirs:
    os.makedirs(os.path.join(base_dir, d), exist_ok=True)

for topic, data in topics_data.items():
    # Concept
    with open(os.path.join(base_dir, "concepts", f"{topic}.json"), "w") as f:
        json.dump(data["concept"], f, indent=2)
    # Formulas
    with open(os.path.join(base_dir, "formulas", f"{topic}.json"), "w") as f:
        json.dump(data["formulas"], f, indent=2)
    # Hints
    with open(os.path.join(base_dir, "hints", f"{topic}.json"), "w") as f:
        json.dump(data["hints"], f, indent=2)
    # Misconceptions
    with open(os.path.join(base_dir, "misconceptions", f"{topic}.json"), "w") as f:
        json.dump(data["misconceptions"], f, indent=2)
    # Experiments
    with open(os.path.join(base_dir, "experiments", f"{topic}.json"), "w") as f:
        json.dump(data["experiments"], f, indent=2)

print("Generated 75 curriculum files successfully!")
