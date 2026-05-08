import math

from .formulas import (
    calculate_time,
    calculate_range,
    calculate_height,
    to_radians,
)


def run_projectile_simulation(
    velocity: float,
    angle: float,
    gravity: float = 9.8
):

    theta = to_radians(angle)

    time = calculate_time(
        velocity,
        angle,
        gravity
    )

    range_ = calculate_range(
        velocity,
        angle,
        gravity
    )

    height = calculate_height(
        velocity,
        angle,
        gravity
    )

    # Impact velocity

    vx = velocity * math.cos(theta)

    vy_final = (
        velocity * math.sin(theta)
        - gravity * time
    )

    impact_velocity = math.sqrt(
        (vx ** 2) + (vy_final ** 2)
    )

    steps = 50

    trajectory = []

    graph = {
        "vx": [],
        "vy": [],
        "y": [],
    }

    for i in range(steps + 1):

        t = (i / steps) * time

        x = vx * t

        y = (
            velocity * math.sin(theta) * t
            - 0.5 * gravity * (t ** 2)
        )

        vy = (
            velocity * math.sin(theta)
            - gravity * t
        )

        trajectory.append({
            "x": round(x, 2),
            "y": round(y, 2),
            "t": round(t, 2),
        })

        graph["vx"].append({
            "t": round(t, 2),
            "value": round(vx, 2)
        })

        graph["vy"].append({
            "t": round(t, 2),
            "value": round(vy, 2)
        })

        graph["y"].append({
            "t": round(t, 2),
            "value": round(y, 2)
        })

    return {
        "time": round(time, 2),
        "range": round(range_, 2),
        "height": round(height, 2),
        "impactVelocity": round(
            impact_velocity,
            2
        ),
        "trajectory": trajectory,
        "graph": graph,
    }