def calculate_acceleration(
    force: float,
    mass: float
) -> float:
    if mass == 0:
        raise ValueError("Mass cannot be zero")
    return force / mass
