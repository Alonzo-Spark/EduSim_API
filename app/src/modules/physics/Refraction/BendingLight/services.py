from .formulas import calculate_refraction


def get_refraction_result(data):

    n1 = data.get("n1")
    n2 = data.get("n2")
    angle1 = data.get("angle1")

    if n1 is None or n2 is None or angle1 is None:
        raise ValueError(
            "Missing required inputs"
        )

    if n1 <= 0 or n2 <= 0:
        raise ValueError(
            "Refractive indices must be positive"
        )

    if angle1 < 0 or angle1 > 90:
        raise ValueError(
            "Angle must be between 0 and 90 degrees"
        )

    return calculate_refraction(
        n1,
        n2,
        angle1
    )