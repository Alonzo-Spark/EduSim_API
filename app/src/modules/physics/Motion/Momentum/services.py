from .formulas import calculate_acceleration

def run_momentum_simulation(
    mass: float,
    force: float
):
    a = calculate_acceleration(force, mass)

    total_time = 5
    steps = 50
    trajectory = []

    for i in range(steps + 1):
        t = (i / steps) * total_time
        v = a * t
        s = 0.5 * a * (t ** 2)

        trajectory.append({
            "t": round(t, 2),
            "v": round(v, 2),
            "a": round(a, 2),
            "f": round(force, 2),
            "x": round(s, 2)
        })

    return {
        "acceleration": round(a, 2),
        "force": round(force, 2),
        "mass": round(mass, 2),
        "trajectory": trajectory
    }
