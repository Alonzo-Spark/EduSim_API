# services.py

import math
from .formulas import (
    calculate_acceleration,
    calculate_normal_force,
    calculate_friction_force,
    to_radians
)

def run_inclined_plane_simulation(angle: float, mass: float, friction: float, gravity: float = 9.8):
    theta = to_radians(angle)

    acceleration = calculate_acceleration(angle, friction, gravity)
    normal_force = calculate_normal_force(mass, angle, gravity)
    friction_force = calculate_friction_force(mass, angle, friction, gravity)

    # NEW: realistic time-based simulation
    total_time = 3  # simulate 3 seconds
    steps = 50

    trajectory = []

    for i in range(steps + 1):
        t = (i / steps) * total_time

        # s = 0.5 * a * t^2
        position = 0.5 * acceleration * t * t

        # OPTIONAL: convert to x,y (for UI visualization)
        x = position * math.cos(theta)
        y = position * math.sin(theta)

        trajectory.append({
            "t": round(t, 2),
            "position": round(position, 2),
            "x": round(x, 2),
            "y": round(y, 2)
        })

    return {
        "acceleration": round(acceleration, 2),
        "normalForce": round(normal_force, 2),
        "frictionForce": round(friction_force, 2),
        "trajectory": trajectory
    }