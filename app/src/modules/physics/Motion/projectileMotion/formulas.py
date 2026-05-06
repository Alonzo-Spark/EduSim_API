import math


def to_radians(deg: float) -> float:
    return (deg * math.pi) / 180


def calculate_time(
    velocity: float,
    angle: float,
    gravity: float = 9.8
) -> float:

    theta = to_radians(angle)

    return (2 * velocity * math.sin(theta)) / gravity


def calculate_range(
    velocity: float,
    angle: float,
    gravity: float = 9.8
) -> float:

    theta = to_radians(angle)

    return (
        velocity * velocity * math.sin(2 * theta)
    ) / gravity


def calculate_height(
    velocity: float,
    angle: float,
    gravity: float = 9.8
) -> float:

    theta = to_radians(angle)

    return (
        velocity * velocity * (math.sin(theta) ** 2)
    ) / (2 * gravity)