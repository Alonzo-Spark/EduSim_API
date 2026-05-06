# formulas.py

import math

def to_radians(deg: float) -> float:
    return (deg * math.pi) / 180

def calculate_acceleration(angle: float, friction: float, g: float = 9.8) -> float:
    theta = to_radians(angle)
    return g * (math.sin(theta) - friction * math.cos(theta))

def calculate_normal_force(mass: float, angle: float, g: float = 9.8) -> float:
    theta = to_radians(angle)
    return mass * g * math.cos(theta)

def calculate_friction_force(mass: float, angle: float, friction: float, g: float = 9.8) -> float:
    normal = calculate_normal_force(mass, angle, g)
    return friction * normal