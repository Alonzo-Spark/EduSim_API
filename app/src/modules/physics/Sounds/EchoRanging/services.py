from .formulas import (
    calculate_distance,
    calculate_echo_time,
    check_echo_heard
)


def run_echo_ranging_simulation(
    speed_of_sound: float,
    echo_time: float,
    obstacle_distance: float
):

    measured_distance = (
        calculate_distance(
            speed_of_sound,
            echo_time
        )
    )

    calculated_echo_time = (
        calculate_echo_time(
            obstacle_distance,
            speed_of_sound
        )
    )

    echo_heard = (
        check_echo_heard(
            calculated_echo_time
        )
    )

    return {

        "measuredDistance":
            measured_distance,

        "echoReturnTime":
            calculated_echo_time,

        "echoHeard":
            echo_heard
    }