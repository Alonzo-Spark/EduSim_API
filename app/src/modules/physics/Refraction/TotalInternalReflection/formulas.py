import math


def deg_to_rad(deg: float) -> float:
    return (deg * math.pi) / 180


def rad_to_deg(rad: float) -> float:
    return (rad * 180) / math.pi


def calculate_tir(
    n1: float,
    n2: float,
    angle1: float
):

    # TIR not possible

    if n1 <= n2:

        return {
            "isTIR": False,
            "criticalAngle": None,
            "reflectionAngle": None,
            "margin": None,
            "direction": "refraction",
            "rays": None,
            "message": (
                "TIR not possible "
                "(n1 must be greater than n2)"
            )
        }

    critical_angle = rad_to_deg(
        math.asin(n2 / n1)
    )

    is_tir = angle1 > critical_angle

    reflection_angle = angle1

    margin = angle1 - critical_angle

    theta = deg_to_rad(angle1)

    # Ray coordinates

    incident_ray = [
        {
            "x": -10,
            "y": round(
                math.tan(theta) * -10,
                2
            )
        },
        {
            "x": 0,
            "y": 0
        }
    ]

    reflected_ray = [
        {
            "x": 0,
            "y": 0
        },
        {
            "x": 10,
            "y": round(
                math.tan(theta) * 10,
                2
            )
        }
    ]

    return {
        "isTIR": is_tir,

        "criticalAngle": round(
            critical_angle,
            2
        ),

        "reflectionAngle": round(
            reflection_angle,
            2
        ),

        "margin": round(
            margin,
            2
        ),

        "direction": (
            "reflection"
            if is_tir
            else "refraction"
        ),

        "rays": (
            {
                "incident": incident_ray,
                "reflected": reflected_ray
            }
            if is_tir
            else None
        )
    }