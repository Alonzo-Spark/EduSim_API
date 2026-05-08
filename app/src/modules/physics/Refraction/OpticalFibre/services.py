from .formulas import (
    calculate_critical_angle,
    check_total_internal_reflection,
    calculate_numerical_aperture,
    calculate_acceptance_angle,
    calculate_speed_in_fibre,
    calculate_transmission_time,
    calculate_attenuation
)


def run_optical_fibre_simulation(
    incident_angle: float,
    core_refractive_index: float,
    cladding_refractive_index: float,
    fibre_length: float,
    initial_intensity: float,
    attenuation_coefficient: float
):

    critical_angle = calculate_critical_angle(
        core_refractive_index,
        cladding_refractive_index
    )

    tir_occurs = False

    if critical_angle is not None:

        tir_occurs = (
            check_total_internal_reflection(
                incident_angle,
                critical_angle
            )
        )

    numerical_aperture = (
        calculate_numerical_aperture(
            core_refractive_index,
            cladding_refractive_index
        )
    )

    acceptance_angle = (
        calculate_acceptance_angle(
            numerical_aperture
        )
    )

    speed = calculate_speed_in_fibre(
        core_refractive_index
    )

    transmission_time = (
        calculate_transmission_time(
            fibre_length,
            speed
        )
    )

    final_intensity = (
        calculate_attenuation(
            initial_intensity,
            attenuation_coefficient,
            fibre_length
        )
    )

    return {

        "criticalAngle": critical_angle,

        "totalInternalReflection": tir_occurs,

        "numericalAperture": numerical_aperture,

        "acceptanceAngle": acceptance_angle,

        "speedInFibre": speed,

        "transmissionTime": transmission_time,

        "finalIntensity": final_intensity
    }