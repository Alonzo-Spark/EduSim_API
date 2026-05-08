import math


def deg_to_rad(deg: float) -> float:
    return (deg * math.pi) / 180


def rad_to_deg(rad: float) -> float:
    return (rad * 180) / math.pi


def calculate_refraction(
    n1: float,
    n2: float,
    angle1: float
):

    theta1 = deg_to_rad(angle1)

    sin_theta2 = (
        (n1 / n2)
        * math.sin(theta1)
    )

    # Direction of bending

    direction = (
        "towards_normal"
        if n2 > n1
        else "away_from_normal"
    )

    # Total Internal Reflection

    if sin_theta2 > 1:

        critical_angle = rad_to_deg(
            math.asin(n2 / n1)
        )

        return {
            "isTIR": True,
            "angle2": None,
            "criticalAngle": round(
                critical_angle,
                2
            ),
            "direction": direction,
            "rays": None
        }

    theta2 = math.asin(sin_theta2)

    # Ray coordinates

    incident_ray = [
        {
            "x": -10,
            "y": round(
                math.tan(theta1) * -10,
                2
            )
        },
        {
            "x": 0,
            "y": 0
        }
    ]

    refracted_ray = [
        {
            "x": 0,
            "y": 0
        },
        {
            "x": 10,
            "y": round(
                math.tan(theta2) * 10,
                2
            )
        }
    ]

    return {
        "isTIR": False,

        "angle2": round(
            rad_to_deg(theta2),
            2
        ),

        "criticalAngle": (
            round(
                rad_to_deg(
                    math.asin(n2 / n1)
                ),
                2
            )
            if n1 > n2
            else None
        ),

        "direction": direction,

        "rays": {
            "incident": incident_ray,
            "refracted": refracted_ray
        }
    }