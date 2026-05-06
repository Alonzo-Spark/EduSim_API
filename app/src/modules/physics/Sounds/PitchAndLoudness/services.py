from .formulas import (
    calculate_period,
    classify_pitch,
    classify_loudness,
    classify_sound_range
)


def run_pitch_and_loudness_simulation(
    frequency: float,
    amplitude: float
):

    period = calculate_period(
        frequency
    )

    pitch = classify_pitch(
        frequency
    )

    loudness = classify_loudness(
        amplitude
    )

    sound_range = classify_sound_range(
        frequency
    )

    return {

        "frequency": frequency,

        "amplitude": amplitude,

        "period": period,

        "pitch": pitch,

        "loudness": loudness,

        "soundRange": sound_range
    }