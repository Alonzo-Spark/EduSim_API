def calculate_distance(
    speed: float,
    time: float
):

    distance = (
        speed * time
    ) / 2

    return round(
        distance,
        2
    )


def calculate_echo_time(
    distance: float,
    speed: float
):

    time = (
        2 * distance
    ) / speed

    return round(
        time,
        3
    )


def check_echo_heard(
    echo_time: float
):

    return echo_time >= 0.1