def calculate_period(
    frequency: float
):

    return round(
        1 / frequency,
        5
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


def classify_sound_range(
    frequency: float
):

    if frequency < 20:
        return "Infrasonic"

    elif frequency <= 20000:
        return "Audible"

    return "Ultrasonic"