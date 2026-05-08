import math


def calculate_wave_y(
    amplitude: float,
    frequency: float,
    x: float
):

    return amplitude * math.sin(
        frequency * x
    )


def classify_pitch(
    frequency: float
):

    if frequency < 250:
        return "Low Pitch"

    elif frequency < 2000:
        return "Medium Pitch"

    return "High Pitch"


def classify_loudness(
    amplitude: float
):

    if amplitude < 3:
        return "Soft"

    elif amplitude < 7:
        return "Moderate"

    return "Loud"