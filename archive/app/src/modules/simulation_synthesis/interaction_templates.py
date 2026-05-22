"""
Reusable runtime interaction templates for Physics DSL generation.

These templates define SEMANTIC PHYSICS INTENT only.
The runtime interpreter is responsible for:
  - motion integration
  - collision resolution
  - rendering
  - animation

Each template defines:
  - type: machine-readable interaction identifier
  - target: the entity ID this interaction applies to
  - parameters: physics-relevant configuration values
"""

# =========================================================
# Standard Interaction Templates
# =========================================================

APPLY_FORCE = {
    "type": "apply_force",
    "target": "",
    "parameters": {
        "force": [0, 0]   # [Fx, Fy] in Newtons
    }
}

GRAVITY = {
    "type": "gravity",
    "target": "",
    "parameters": {
        "g": 9.8          # gravitational acceleration m/s^2
    }
}

FRICTION = {
    "type": "friction",
    "target": "",
    "parameters": {
        "mu_kinetic": 0.3,
        "mu_static": 0.4
    }
}

NORMAL_FORCE = {
    "type": "normal_force",
    "target": "",
    "parameters": {
        "surface_normal": [0, 1]  # unit vector
    }
}

COLLISION = {
    "type": "collision",
    "target": "",
    "parameters": {
        "with_entity": "",
        "restitution": 1.0   # 1.0 = perfectly elastic, 0.0 = perfectly inelastic
    }
}

PROJECTILE_LAUNCH = {
    "type": "projectile_launch",
    "target": "",
    "parameters": {
        "angle_deg": 45.0,
        "initial_speed": 20.0   # m/s
    }
}

SPRING_FORCE = {
    "type": "spring_force",
    "target": "",
    "parameters": {
        "spring_constant": 100.0,  # N/m
        "natural_length": 1.0,     # m
        "anchor": [0, 0]
    }
}

TORQUE = {
    "type": "torque",
    "target": "",
    "parameters": {
        "moment": 0.0,    # N·m
        "pivot": [0, 0]
    }
}

INCLINE = {
    "type": "incline",
    "target": "",
    "parameters": {
        "angle_deg": 30.0   # angle of inclined surface in degrees
    }
}


# =========================================================
# Canonical Template Registry
# (Used by prompt_builder for example generation)
# =========================================================

INTERACTION_REGISTRY = {
    "apply_force":       APPLY_FORCE,
    "gravity":           GRAVITY,
    "friction":          FRICTION,
    "normal_force":      NORMAL_FORCE,
    "collision":         COLLISION,
    "projectile_launch": PROJECTILE_LAUNCH,
    "spring_force":      SPRING_FORCE,
    "torque":            TORQUE,
    "incline":           INCLINE,
}


# =========================================================
# Standardized Vocabularies
# =========================================================

ALLOWED_ENTITY_TYPES = {
    "block",
    "sphere",
    "projectile",
    "pendulum",
    "spring",
    "plane",
    "particle",
}

ALLOWED_VISUALIZATION_TYPES = {
    "force_vectors",
    "velocity_graph",
    "acceleration_graph",
    "trajectory_path",
    "energy_bar",
    "motion_trace",
}
