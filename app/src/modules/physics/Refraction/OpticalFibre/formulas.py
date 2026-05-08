import math


# Speed of light in vacuum
C = 3 * 10**8


def calculate_critical_angle(
    n1: float,
    n2: float
):

    if n1 <= n2:
        return None

    critical_angle = math.degrees(
        math.asin(n2 / n1)
    )

    return round(
        critical_angle,
        2
    )


def check_total_internal_reflection(
    incident_angle: float,
    critical_angle: float
):

    return incident_angle > critical_angle


def calculate_numerical_aperture(
    n1: float,
    n2: float
):

    na = math.sqrt(
        (n1 ** 2) - (n2 ** 2)
    )

    return round(
        na,
        4
    )


def calculate_acceptance_angle(
    numerical_aperture: float
):

    angle = math.degrees(
        math.asin(numerical_aperture)
    )

    return round(
        angle,
        2
    )


def calculate_speed_in_fibre(
    refractive_index: float
):

    speed = C / refractive_index

    return round(
        speed,
        2
    )


def calculate_transmission_time(
    distance: float,
    speed: float
):

    time = distance / speed

    return format(time, ".9f")


def calculate_attenuation(
    initial_intensity: float,
    attenuation_coefficient: float,
    distance: float
):

    final_intensity = (
        initial_intensity *
        math.exp(
            -attenuation_coefficient * distance
        )
    )

    return round(
        final_intensity,
        4
    )