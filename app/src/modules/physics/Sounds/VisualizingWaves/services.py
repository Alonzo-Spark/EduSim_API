from .formulas import (
    calculate_wave_y,
    classify_pitch,
    classify_loudness
)


def run_wave_visualization_simulation(
    amplitude: float,
    frequency: float
):

    wave_points = []

    for x in range(100):

        scaled_x = x / 10

        y = calculate_wave_y(
            amplitude,
            frequency / 10,
            scaled_x
        )

        wave_points.append({

            "x": round(scaled_x, 2),

            "y": round(y, 2)
        })

    pitch = classify_pitch(
        frequency
    )

    loudness = classify_loudness(
        amplitude
    )

    return {

        "pitch": pitch,

        "loudness": loudness,

        "wavePoints": wave_points
    }