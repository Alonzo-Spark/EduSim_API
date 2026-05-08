from .formulas import calculate_acceleration


def run_action_reaction_simulation(
    mass1: float,
    mass2: float,
    force: float
):

    a1 = calculate_acceleration(force, mass1)
    a2 = calculate_acceleration(force, mass2)

    total_time = 3
    steps = 50

    object1 = []
    object2 = []

    for i in range(steps + 1):

        t = (i / steps) * total_time

        s1 = 0.5 * a1 * (t ** 2)
        s2 = 0.5 * a2 * (t ** 2)

        object1.append({
            "t": round(t, 2),
            "position": round(s1, 2)
        })

        object2.append({
            "t": round(t, 2),
            "position": round(-s2, 2)
        })

    return {
        "acceleration1": round(a1, 2),
        "acceleration2": round(a2, 2),
        "trajectories": {
            "object1": object1,
            "object2": object2
        }
    }